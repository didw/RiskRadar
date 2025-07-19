"""경로 탐색 알고리즘"""
import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
import heapq

from src.neo4j.session import session

logger = logging.getLogger(__name__)


@dataclass
class PathNode:
    """경로 노드 정보"""
    id: str
    name: str
    type: str
    risk_score: float
    properties: Dict


@dataclass
class PathRelationship:
    """경로 관계 정보"""
    type: str
    properties: Dict
    strength: Optional[float]
    confidence: Optional[float]


@dataclass
class RiskPath:
    """리스크 경로"""
    nodes: List[PathNode]
    relationships: List[PathRelationship]
    total_length: int
    risk_score: float
    path_type: str  # DIRECT, INDIRECT, CASCADING
    risk_factors: List[str]


@dataclass
class PathAnalysisResult:
    """경로 분석 결과"""
    source_node: PathNode
    target_node: PathNode
    paths: List[RiskPath]
    shortest_path_length: int
    highest_risk_path: RiskPath
    total_paths_found: int


class PathFinder:
    """경로 탐색기"""
    
    def __init__(self):
        self.session = session
    
    def find_shortest_paths(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 6,
        relationship_types: Optional[List[str]] = None
    ) -> List[RiskPath]:
        """최단 경로 찾기
        
        Args:
            source_id: 시작 노드 ID
            target_id: 목표 노드 ID
            max_length: 최대 경로 길이
            relationship_types: 사용할 관계 타입
            
        Returns:
            최단 경로 리스트
        """
        try:
            # Build relationship filter
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_filter = f":{rel_types}"
            
            query = f"""
            MATCH (source {{id: $source_id}}), (target {{id: $target_id}})
            MATCH path = allShortestPaths((source)-[{rel_filter}*1..{max_length}]-(target))
            
            WITH path, nodes(path) as path_nodes, relationships(path) as path_rels
            
            RETURN 
                [node in path_nodes | {{
                    id: node.id,
                    name: node.name,
                    type: labels(node)[0],
                    risk_score: node.risk_score,
                    properties: properties(node)
                }}] as nodes,
                [rel in path_rels | {{
                    type: type(rel),
                    properties: properties(rel),
                    strength: rel.strength,
                    confidence: rel.confidence
                }}] as relationships,
                length(path) as path_length
            
            ORDER BY path_length
            LIMIT 10
            """
            
            results = self.session.run_query(
                query,
                source_id=source_id,
                target_id=target_id
            )
            
            paths = []
            for row in results:
                risk_path = self._create_risk_path(
                    row['nodes'],
                    row['relationships'],
                    row['path_length']
                )
                paths.append(risk_path)
            
            return paths
            
        except Exception as e:
            logger.error(f"Error finding shortest paths: {e}")
            return []
    
    def find_risk_propagation_paths(
        self,
        source_id: str,
        min_risk_threshold: float = 6.0,
        max_depth: int = 4,
        max_paths: int = 20
    ) -> List[RiskPath]:
        """리스크 전파 경로 찾기
        
        Args:
            source_id: 시작 노드 ID
            min_risk_threshold: 최소 리스크 임계값
            max_depth: 최대 탐색 깊이
            max_paths: 최대 경로 수
            
        Returns:
            리스크 전파 경로 리스트
        """
        try:
            query = f"""
            MATCH (source {{id: $source_id}})
            MATCH path = (source)-[*1..{max_depth}]-(target)
            
            WHERE target.risk_score >= {min_risk_threshold}
            AND source <> target
            
            WITH path, nodes(path) as path_nodes, relationships(path) as path_rels,
                 reduce(total_risk = 0.0, node in nodes(path) | 
                   total_risk + COALESCE(node.risk_score, 5.0)) as total_path_risk
            
            WHERE size(path_nodes) > 1
            
            RETURN 
                [node in path_nodes | {{
                    id: node.id,
                    name: node.name,
                    type: labels(node)[0],
                    risk_score: node.risk_score,
                    properties: properties(node)
                }}] as nodes,
                [rel in path_rels | {{
                    type: type(rel),
                    properties: properties(rel),
                    strength: rel.strength,
                    confidence: rel.confidence
                }}] as relationships,
                length(path) as path_length,
                total_path_risk,
                total_path_risk / length(path) as avg_path_risk
            
            ORDER BY avg_path_risk DESC, path_length ASC
            LIMIT {max_paths}
            """
            
            results = self.session.run_query(
                query,
                source_id=source_id
            )
            
            paths = []
            for row in results:
                risk_path = self._create_risk_path(
                    row['nodes'],
                    row['relationships'],
                    row['path_length'],
                    path_type="CASCADING"
                )
                risk_path.risk_score = row['avg_path_risk']
                paths.append(risk_path)
            
            return paths
            
        except Exception as e:
            logger.error(f"Error finding risk propagation paths: {e}")
            return []
    
    def find_critical_paths(
        self,
        source_id: str,
        target_id: str,
        criticality_factors: Optional[Dict] = None
    ) -> PathAnalysisResult:
        """중요 경로 분석
        
        Args:
            source_id: 시작 노드 ID
            target_id: 목표 노드 ID
            criticality_factors: 중요도 요인
            
        Returns:
            경로 분석 결과
        """
        try:
            # Default criticality factors
            if not criticality_factors:
                criticality_factors = {
                    'risk_weight': 0.4,
                    'connection_weight': 0.3,
                    'sector_weight': 0.3
                }
            
            query = """
            MATCH (source {id: $source_id}), (target {id: $target_id})
            MATCH path = (source)-[*1..5]-(target)
            
            WITH path, nodes(path) as path_nodes, relationships(path) as path_rels,
                 reduce(total_risk = 0.0, node in nodes(path) | 
                   total_risk + COALESCE(node.risk_score, 5.0)) as total_risk,
                 reduce(total_connections = 0, node in nodes(path) | 
                   total_connections + size((node)--()) ) as total_connections
            
            WITH path, path_nodes, path_rels, total_risk, total_connections,
                 (total_risk * $risk_weight + 
                  total_connections * $connection_weight) / length(path) as criticality_score
            
            RETURN 
                [node in path_nodes | {
                    id: node.id,
                    name: node.name,
                    type: labels(node)[0],
                    risk_score: node.risk_score,
                    properties: properties(node)
                }] as nodes,
                [rel in path_rels | {
                    type: type(rel),
                    properties: properties(rel),
                    strength: rel.strength,
                    confidence: rel.confidence
                }] as relationships,
                length(path) as path_length,
                total_risk / length(path) as avg_risk,
                criticality_score
            
            ORDER BY criticality_score DESC
            LIMIT 15
            """
            
            results = self.session.run_query(
                query,
                source_id=source_id,
                target_id=target_id,
                risk_weight=criticality_factors['risk_weight'],
                connection_weight=criticality_factors['connection_weight']
            )
            
            if not results:
                return self._create_empty_analysis_result(source_id, target_id)
            
            # Create risk paths
            paths = []
            for row in results:
                risk_path = self._create_risk_path(
                    row['nodes'],
                    row['relationships'],
                    row['path_length']
                )
                risk_path.risk_score = row['avg_risk']
                paths.append(risk_path)
            
            # Find source and target nodes
            source_node = self._get_node_info(source_id)
            target_node = self._get_node_info(target_id)
            
            # Analysis results
            shortest_length = min(p.total_length for p in paths) if paths else 0
            highest_risk = max(paths, key=lambda p: p.risk_score) if paths else None
            
            return PathAnalysisResult(
                source_node=source_node,
                target_node=target_node,
                paths=paths,
                shortest_path_length=shortest_length,
                highest_risk_path=highest_risk,
                total_paths_found=len(paths)
            )
            
        except Exception as e:
            logger.error(f"Error finding critical paths: {e}")
            return self._create_empty_analysis_result(source_id, target_id)
    
    def analyze_bottleneck_nodes(
        self,
        node_types: Optional[List[str]] = None,
        min_path_count: int = 5
    ) -> List[Dict]:
        """병목 노드 분석
        
        Args:
            node_types: 분석할 노드 타입
            min_path_count: 최소 경로 수
            
        Returns:
            병목 노드 정보 리스트
        """
        try:
            node_filter = ""
            if node_types:
                labels_condition = " OR ".join([f"'{nt}' IN labels(n)" for nt in node_types])
                node_filter = f"WHERE {labels_condition}"
            
            query = f"""
            MATCH (n) {node_filter}
            
            // Count paths passing through this node
            MATCH path = ()-[*2..4]-(other)
            WHERE n IN nodes(path) AND n <> head(nodes(path)) AND n <> last(nodes(path))
            
            WITH n, count(DISTINCT path) as path_count
            WHERE path_count >= {min_path_count}
            
            // Get node connectivity
            MATCH (n)-[r]-()
            WITH n, path_count, count(r) as degree
            
            RETURN 
                n.id as node_id,
                n.name as node_name,
                labels(n)[0] as node_type,
                n.risk_score as risk_score,
                path_count,
                degree,
                (path_count * 0.6 + degree * 0.4) as bottleneck_score
            
            ORDER BY bottleneck_score DESC
            LIMIT 20
            """
            
            results = self.session.run_query(query)
            
            bottlenecks = []
            for row in results:
                bottleneck_info = {
                    'node_id': row['node_id'],
                    'node_name': row['node_name'],
                    'node_type': row['node_type'],
                    'risk_score': row['risk_score'],
                    'path_count': row['path_count'],
                    'degree': row['degree'],
                    'bottleneck_score': row['bottleneck_score'],
                    'criticality': self._categorize_bottleneck_criticality(row['bottleneck_score'])
                }
                bottlenecks.append(bottleneck_info)
            
            return bottlenecks
            
        except Exception as e:
            logger.error(f"Error analyzing bottleneck nodes: {e}")
            return []
    
    def find_alternative_paths(
        self,
        source_id: str,
        target_id: str,
        blocked_nodes: Optional[List[str]] = None,
        max_length: int = 6
    ) -> List[RiskPath]:
        """대안 경로 찾기 (특정 노드 차단 시)
        
        Args:
            source_id: 시작 노드 ID
            target_id: 목표 노드 ID
            blocked_nodes: 차단할 노드 ID 리스트
            max_length: 최대 경로 길이
            
        Returns:
            대안 경로 리스트
        """
        try:
            # Build blocked nodes filter
            blocked_filter = ""
            if blocked_nodes:
                blocked_filter = f"AND NOT any(node in nodes(path) WHERE node.id IN {blocked_nodes})"
            
            query = f"""
            MATCH (source {{id: $source_id}}), (target {{id: $target_id}})
            MATCH path = (source)-[*1..{max_length}]-(target)
            
            WHERE source <> target {blocked_filter}
            
            WITH path, nodes(path) as path_nodes, relationships(path) as path_rels,
                 reduce(total_risk = 0.0, node in nodes(path) | 
                   total_risk + COALESCE(node.risk_score, 5.0)) as total_risk
            
            RETURN 
                [node in path_nodes | {{
                    id: node.id,
                    name: node.name,
                    type: labels(node)[0],
                    risk_score: node.risk_score,
                    properties: properties(node)
                }}] as nodes,
                [rel in path_rels | {{
                    type: type(rel),
                    properties: properties(rel),
                    strength: rel.strength,
                    confidence: rel.confidence
                }}] as relationships,
                length(path) as path_length,
                total_risk / length(path) as avg_risk
            
            ORDER BY path_length ASC, avg_risk ASC
            LIMIT 10
            """
            
            results = self.session.run_query(
                query,
                source_id=source_id,
                target_id=target_id
            )
            
            paths = []
            for row in results:
                risk_path = self._create_risk_path(
                    row['nodes'],
                    row['relationships'],
                    row['path_length'],
                    path_type="ALTERNATIVE"
                )
                risk_path.risk_score = row['avg_risk']
                paths.append(risk_path)
            
            return paths
            
        except Exception as e:
            logger.error(f"Error finding alternative paths: {e}")
            return []
    
    def calculate_path_resilience(
        self,
        source_id: str,
        target_id: str,
        failure_scenarios: Optional[List[Dict]] = None
    ) -> Dict:
        """경로 복원력 계산
        
        Args:
            source_id: 시작 노드 ID
            target_id: 목표 노드 ID
            failure_scenarios: 장애 시나리오 리스트
            
        Returns:
            경로 복원력 분석 결과
        """
        try:
            # Default failure scenarios
            if not failure_scenarios:
                failure_scenarios = [
                    {'type': 'single_node', 'probability': 0.1},
                    {'type': 'sector_failure', 'probability': 0.05},
                    {'type': 'high_risk_nodes', 'probability': 0.2}
                ]
            
            # Find all paths
            all_paths = self.find_shortest_paths(source_id, target_id)
            
            if not all_paths:
                return {
                    'source_id': source_id,
                    'target_id': target_id,
                    'resilience_score': 0.0,
                    'path_diversity': 0,
                    'failure_impact': {},
                    'recommendations': ["No paths found between nodes"]
                }
            
            # Calculate path diversity
            unique_intermediate_nodes = set()
            for path in all_paths:
                # Exclude source and target from intermediate nodes
                intermediate = path.nodes[1:-1] if len(path.nodes) > 2 else []
                unique_intermediate_nodes.update(node.id for node in intermediate)
            
            path_diversity = len(unique_intermediate_nodes)
            
            # Simulate failure scenarios
            failure_impact = {}
            for scenario in failure_scenarios:
                impact = self._simulate_failure_scenario(
                    source_id, target_id, all_paths, scenario
                )
                failure_impact[scenario['type']] = impact
            
            # Calculate overall resilience score
            base_resilience = min(len(all_paths) / 5.0, 1.0)  # Normalized by max 5 paths
            diversity_bonus = min(path_diversity / 10.0, 0.2)  # Max 20% bonus
            failure_penalty = sum(impact['connectivity_loss'] * scenario['probability'] 
                                for scenario, impact in zip(failure_scenarios, failure_impact.values()))
            
            resilience_score = max(base_resilience + diversity_bonus - failure_penalty, 0.0)
            
            # Generate recommendations
            recommendations = self._generate_resilience_recommendations(
                resilience_score, path_diversity, failure_impact
            )
            
            return {
                'source_id': source_id,
                'target_id': target_id,
                'resilience_score': resilience_score,
                'path_diversity': path_diversity,
                'total_paths': len(all_paths),
                'failure_impact': failure_impact,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error calculating path resilience: {e}")
            return {
                'source_id': source_id,
                'target_id': target_id,
                'error': str(e)
            }
    
    def _create_risk_path(
        self,
        nodes: List[Dict],
        relationships: List[Dict],
        length: int,
        path_type: str = "DIRECT"
    ) -> RiskPath:
        """리스크 경로 생성"""
        path_nodes = [
            PathNode(
                id=node['id'],
                name=node['name'],
                type=node['type'],
                risk_score=node['risk_score'] or 5.0,
                properties=node['properties']
            )
            for node in nodes
        ]
        
        path_rels = [
            PathRelationship(
                type=rel['type'],
                properties=rel['properties'],
                strength=rel.get('strength'),
                confidence=rel.get('confidence')
            )
            for rel in relationships
        ]
        
        # Calculate path risk score
        risk_scores = [node.risk_score for node in path_nodes]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 5.0
        
        # Identify risk factors
        risk_factors = []
        for node in path_nodes:
            if node.risk_score >= 7.0:
                risk_factors.append(f"High risk {node.type}: {node.name}")
        
        return RiskPath(
            nodes=path_nodes,
            relationships=path_rels,
            total_length=length,
            risk_score=avg_risk,
            path_type=path_type,
            risk_factors=risk_factors
        )
    
    def _get_node_info(self, node_id: str) -> PathNode:
        """노드 정보 조회"""
        try:
            query = """
            MATCH (n {id: $node_id})
            RETURN 
                n.id as id,
                n.name as name,
                labels(n)[0] as type,
                n.risk_score as risk_score,
                properties(n) as properties
            """
            
            result = self.session.run_query(query, node_id=node_id)
            
            if result:
                row = result[0]
                return PathNode(
                    id=row['id'],
                    name=row['name'],
                    type=row['type'],
                    risk_score=row['risk_score'] or 5.0,
                    properties=row['properties']
                )
            else:
                return PathNode(
                    id=node_id,
                    name="Unknown",
                    type="Unknown",
                    risk_score=5.0,
                    properties={}
                )
                
        except Exception as e:
            logger.error(f"Error getting node info: {e}")
            return PathNode(
                id=node_id,
                name="Unknown",
                type="Unknown",
                risk_score=5.0,
                properties={}
            )
    
    def _create_empty_analysis_result(self, source_id: str, target_id: str) -> PathAnalysisResult:
        """빈 분석 결과 생성"""
        source_node = self._get_node_info(source_id)
        target_node = self._get_node_info(target_id)
        
        return PathAnalysisResult(
            source_node=source_node,
            target_node=target_node,
            paths=[],
            shortest_path_length=0,
            highest_risk_path=None,
            total_paths_found=0
        )
    
    def _categorize_bottleneck_criticality(self, score: float) -> str:
        """병목 중요도 분류"""
        if score >= 50:
            return "CRITICAL"
        elif score >= 20:
            return "HIGH"
        elif score >= 10:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _simulate_failure_scenario(
        self,
        source_id: str,
        target_id: str,
        paths: List[RiskPath],
        scenario: Dict
    ) -> Dict:
        """장애 시나리오 시뮬레이션"""
        scenario_type = scenario['type']
        
        if scenario_type == 'single_node':
            # Most connected node failure
            return self._simulate_single_node_failure(paths)
        elif scenario_type == 'sector_failure':
            # Sector-wide failure
            return self._simulate_sector_failure(paths)
        elif scenario_type == 'high_risk_nodes':
            # High risk nodes failure
            return self._simulate_high_risk_failure(paths)
        else:
            return {'connectivity_loss': 0.0, 'affected_paths': 0}
    
    def _simulate_single_node_failure(self, paths: List[RiskPath]) -> Dict:
        """단일 노드 장애 시뮬레이션"""
        if not paths:
            return {'connectivity_loss': 1.0, 'affected_paths': 0}
        
        # Find most critical intermediate node
        node_frequency = {}
        for path in paths:
            for node in path.nodes[1:-1]:  # Exclude source and target
                node_frequency[node.id] = node_frequency.get(node.id, 0) + 1
        
        if not node_frequency:
            return {'connectivity_loss': 0.0, 'affected_paths': 0}
        
        # Remove most frequent node
        critical_node = max(node_frequency, key=node_frequency.get)
        affected_paths = node_frequency[critical_node]
        
        connectivity_loss = affected_paths / len(paths)
        
        return {
            'connectivity_loss': connectivity_loss,
            'affected_paths': affected_paths,
            'critical_node': critical_node
        }
    
    def _simulate_sector_failure(self, paths: List[RiskPath]) -> Dict:
        """섹터 장애 시뮬레이션"""
        if not paths:
            return {'connectivity_loss': 1.0, 'affected_paths': 0}
        
        # Find most common sector in intermediate nodes
        sector_frequency = {}
        for path in paths:
            path_sectors = set()
            for node in path.nodes[1:-1]:
                sector = node.properties.get('sector')
                if sector:
                    path_sectors.add(sector)
            
            for sector in path_sectors:
                sector_frequency[sector] = sector_frequency.get(sector, 0) + 1
        
        if not sector_frequency:
            return {'connectivity_loss': 0.0, 'affected_paths': 0}
        
        # Most critical sector
        critical_sector = max(sector_frequency, key=sector_frequency.get)
        affected_paths = sector_frequency[critical_sector]
        
        connectivity_loss = affected_paths / len(paths)
        
        return {
            'connectivity_loss': connectivity_loss,
            'affected_paths': affected_paths,
            'critical_sector': critical_sector
        }
    
    def _simulate_high_risk_failure(self, paths: List[RiskPath]) -> Dict:
        """고위험 노드 장애 시뮬레이션"""
        if not paths:
            return {'connectivity_loss': 1.0, 'affected_paths': 0}
        
        affected_paths = 0
        high_risk_nodes = []
        
        for path in paths:
            path_affected = False
            for node in path.nodes:
                if node.risk_score >= 7.0:
                    high_risk_nodes.append(node.id)
                    path_affected = True
                    break
            
            if path_affected:
                affected_paths += 1
        
        connectivity_loss = affected_paths / len(paths)
        
        return {
            'connectivity_loss': connectivity_loss,
            'affected_paths': affected_paths,
            'high_risk_nodes': list(set(high_risk_nodes))
        }
    
    def _generate_resilience_recommendations(
        self,
        resilience_score: float,
        path_diversity: int,
        failure_impact: Dict
    ) -> List[str]:
        """복원력 권장사항 생성"""
        recommendations = []
        
        if resilience_score < 0.3:
            recommendations.append("경로 다양성 확보를 위한 추가 연결 구축 필요")
        
        if path_diversity < 3:
            recommendations.append("대안 경로 개발을 통한 단일 장애점 위험 완화")
        
        for scenario, impact in failure_impact.items():
            if impact['connectivity_loss'] > 0.5:
                recommendations.append(f"{scenario} 시나리오에 대한 백업 계획 수립")
        
        if resilience_score > 0.8:
            recommendations.append("우수한 경로 복원력 - 현재 수준 유지")
        
        return recommendations


# 싱글톤 인스턴스
pathfinder = PathFinder()
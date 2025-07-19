"""커뮤니티 탐지 알고리즘"""
import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

from src.neo4j.session import session

logger = logging.getLogger(__name__)


@dataclass
class Community:
    """커뮤니티 정보"""
    id: int
    nodes: List[str]
    size: int
    density: float
    avg_risk_score: float
    dominant_sector: Optional[str]
    risk_level: str  # LOW, MEDIUM, HIGH


@dataclass
class CommunityAnalysisResult:
    """커뮤니티 분석 결과"""
    communities: List[Community]
    modularity: float
    total_communities: int
    largest_community_size: int
    avg_community_size: float


class CommunityDetector:
    """커뮤니티 탐지기"""
    
    def __init__(self):
        self.session = session
    
    def detect_communities_louvain(
        self,
        node_types: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None,
        min_community_size: int = 3
    ) -> CommunityAnalysisResult:
        """Louvain 알고리즘을 사용한 커뮤니티 탐지
        
        Args:
            node_types: 분석할 노드 타입
            relationship_types: 분석할 관계 타입
            min_community_size: 최소 커뮤니티 크기
            
        Returns:
            커뮤니티 분석 결과
        """
        try:
            # Graph projection for Louvain
            node_projection = "*, ".join(node_types) if node_types else "*"
            rel_projection = "*, ".join(relationship_types) if relationship_types else "*"
            
            projection_query = f"""
            CALL gds.graph.project(
                'community-graph',
                ['{node_projection}'],
                ['{rel_projection}']
            )
            """
            
            self.session.run_query(projection_query)
            
            # Run Louvain algorithm
            louvain_query = """
            CALL gds.louvain.stream('community-graph')
            YIELD nodeId, communityId
            
            MATCH (n) WHERE id(n) = nodeId
            RETURN 
                n.id as node_id,
                n.name as node_name,
                labels(n)[0] as node_type,
                n.risk_score as risk_score,
                n.sector as sector,
                communityId
            """
            
            results = self.session.run_query(louvain_query)
            
            # Clean up projected graph
            self.session.run_query("CALL gds.graph.drop('community-graph')")
            
            # Process results into communities
            communities = self._process_community_results(results, min_community_size)
            
            # Calculate modularity (approximation)
            modularity = self._calculate_modularity_approximation(communities)
            
            return CommunityAnalysisResult(
                communities=communities,
                modularity=modularity,
                total_communities=len(communities),
                largest_community_size=max(c.size for c in communities) if communities else 0,
                avg_community_size=sum(c.size for c in communities) / len(communities) if communities else 0
            )
            
        except Exception as e:
            logger.error(f"Error in Louvain community detection: {e}")
            return self._fallback_community_detection(node_types, min_community_size)
    
    def detect_risk_communities(
        self,
        min_risk_threshold: float = 6.0,
        max_depth: int = 3,
        min_community_size: int = 3
    ) -> List[Community]:
        """리스크 기반 커뮤니티 탐지
        
        Args:
            min_risk_threshold: 최소 리스크 임계값
            max_depth: 최대 탐색 깊이
            min_community_size: 최소 커뮤니티 크기
            
        Returns:
            리스크 커뮤니티 리스트
        """
        try:
            # Find high-risk nodes
            high_risk_query = f"""
            MATCH (n)
            WHERE n.risk_score >= {min_risk_threshold}
            RETURN n.id as node_id, n.risk_score as risk_score
            """
            
            high_risk_nodes = self.session.run_query(high_risk_query)
            
            if not high_risk_nodes:
                return []
            
            # Build risk communities using connected components
            communities = []
            visited = set()
            
            for node_data in high_risk_nodes:
                node_id = node_data['node_id']
                
                if node_id not in visited:
                    # Find connected high-risk subgraph
                    community_nodes = self._find_risk_connected_component(
                        node_id, min_risk_threshold, max_depth, visited
                    )
                    
                    if len(community_nodes) >= min_community_size:
                        community = self._create_risk_community(
                            len(communities), community_nodes
                        )
                        communities.append(community)
                    
                    visited.update(community_nodes)
            
            return communities
            
        except Exception as e:
            logger.error(f"Error detecting risk communities: {e}")
            return []
    
    def find_sector_clusters(
        self,
        sector: str,
        min_cluster_size: int = 5
    ) -> List[Dict]:
        """섹터별 클러스터 찾기
        
        Args:
            sector: 대상 섹터
            min_cluster_size: 최소 클러스터 크기
            
        Returns:
            섹터 클러스터 정보 리스트
        """
        try:
            query = f"""
            // Find companies in the sector
            MATCH (c:Company {{sector: $sector}})
            
            // Find their connections
            OPTIONAL MATCH path = (c)-[*1..2]-(connected:Company {{sector: $sector}})
            
            WITH c, collect(DISTINCT connected.id) as connected_ids
            WHERE size(connected_ids) >= {min_cluster_size - 1}
            
            RETURN 
                c.id as center_id,
                c.name as center_name,
                c.risk_score as center_risk,
                connected_ids,
                size(connected_ids) as cluster_size
            
            ORDER BY cluster_size DESC
            """
            
            results = self.session.run_query(query, sector=sector)
            
            clusters = []
            for row in results:
                cluster_info = {
                    'center_id': row['center_id'],
                    'center_name': row['center_name'],
                    'center_risk': row['center_risk'],
                    'sector': sector,
                    'cluster_size': row['cluster_size'],
                    'connected_companies': row['connected_ids']
                }
                clusters.append(cluster_info)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error finding sector clusters: {e}")
            return []
    
    def analyze_community_risks(
        self,
        community: Community,
        include_external_risks: bool = True
    ) -> Dict:
        """커뮤니티 리스크 분석
        
        Args:
            community: 분석할 커뮤니티
            include_external_risks: 외부 리스크 포함 여부
            
        Returns:
            커뮤니티 리스크 분석 결과
        """
        try:
            # Internal community risks
            internal_query = """
            MATCH (n) WHERE n.id IN $node_ids
            OPTIONAL MATCH (n)-[:EXPOSED_TO]->(risk:Risk)
            
            RETURN 
                avg(n.risk_score) as avg_internal_risk,
                collect(DISTINCT {
                    category: risk.category,
                    level: risk.level,
                    description: risk.description
                }) as internal_risks,
                count(DISTINCT risk) as risk_count
            """
            
            internal_result = self.session.run_query(
                internal_query, 
                node_ids=community.nodes
            )
            
            analysis = {
                'community_id': community.id,
                'community_size': community.size,
                'avg_internal_risk': internal_result[0]['avg_internal_risk'] if internal_result else 0.0,
                'internal_risks': internal_result[0]['internal_risks'] if internal_result else [],
                'risk_count': internal_result[0]['risk_count'] if internal_result else 0
            }
            
            if include_external_risks:
                # External risks from connected entities
                external_query = """
                MATCH (internal) WHERE internal.id IN $node_ids
                MATCH (internal)-[*1..2]-(external)
                WHERE NOT external.id IN $node_ids
                
                OPTIONAL MATCH (external)-[:EXPOSED_TO]->(risk:Risk)
                
                RETURN 
                    avg(external.risk_score) as avg_external_risk,
                    collect(DISTINCT {
                        entity_id: external.id,
                        entity_name: external.name,
                        risk_score: external.risk_score
                    }) as external_entities,
                    collect(DISTINCT {
                        category: risk.category,
                        level: risk.level
                    }) as external_risks
                """
                
                external_result = self.session.run_query(
                    external_query,
                    node_ids=community.nodes
                )
                
                if external_result:
                    analysis.update({
                        'avg_external_risk': external_result[0]['avg_external_risk'],
                        'external_entities': external_result[0]['external_entities'][:10],  # Top 10
                        'external_risks': external_result[0]['external_risks']
                    })
            
            # Risk assessment
            overall_risk = analysis['avg_internal_risk']
            if include_external_risks and 'avg_external_risk' in analysis:
                overall_risk = (analysis['avg_internal_risk'] * 0.7 + 
                              analysis['avg_external_risk'] * 0.3)
            
            analysis['overall_risk_level'] = self._categorize_risk_level(overall_risk)
            analysis['risk_recommendations'] = self._generate_risk_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing community risks: {e}")
            return {
                'community_id': community.id,
                'error': str(e)
            }
    
    def _process_community_results(
        self,
        results: List[Dict],
        min_community_size: int
    ) -> List[Community]:
        """커뮤니티 결과 처리"""
        community_groups = defaultdict(list)
        
        # Group nodes by community ID
        for row in results:
            community_id = row['communityId']
            community_groups[community_id].append(row)
        
        communities = []
        community_counter = 0
        
        for comm_id, nodes in community_groups.items():
            if len(nodes) >= min_community_size:
                node_ids = [node['node_id'] for node in nodes]
                risk_scores = [node['risk_score'] for node in nodes if node['risk_score']]
                sectors = [node['sector'] for node in nodes if node['sector']]
                
                # Calculate community metrics
                avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 5.0
                dominant_sector = max(set(sectors), key=sectors.count) if sectors else None
                
                # Calculate density (approximation)
                density = self._calculate_community_density(node_ids)
                
                community = Community(
                    id=community_counter,
                    nodes=node_ids,
                    size=len(nodes),
                    density=density,
                    avg_risk_score=avg_risk,
                    dominant_sector=dominant_sector,
                    risk_level=self._categorize_risk_level(avg_risk)
                )
                
                communities.append(community)
                community_counter += 1
        
        return communities
    
    def _find_risk_connected_component(
        self,
        start_node: str,
        min_risk_threshold: float,
        max_depth: int,
        visited: Set[str]
    ) -> List[str]:
        """리스크 연결 컴포넌트 찾기 (DFS)"""
        try:
            query = f"""
            MATCH path = (start {{id: $start_id}})-[*1..{max_depth}]-(connected)
            WHERE connected.risk_score >= {min_risk_threshold}
            AND NOT connected.id IN $visited_nodes
            
            RETURN collect(DISTINCT connected.id) as component_nodes
            """
            
            result = self.session.run_query(
                query,
                start_id=start_node,
                visited_nodes=list(visited)
            )
            
            if result and result[0]['component_nodes']:
                component_nodes = result[0]['component_nodes']
                component_nodes.append(start_node)  # Include start node
                return component_nodes
            else:
                return [start_node]
                
        except Exception as e:
            logger.error(f"Error finding risk connected component: {e}")
            return [start_node]
    
    def _create_risk_community(
        self,
        community_id: int,
        node_ids: List[str]
    ) -> Community:
        """리스크 커뮤니티 생성"""
        try:
            # Get node details
            query = """
            MATCH (n) WHERE n.id IN $node_ids
            RETURN 
                avg(n.risk_score) as avg_risk,
                collect(DISTINCT n.sector) as sectors
            """
            
            result = self.session.run_query(query, node_ids=node_ids)
            
            if result:
                avg_risk = result[0]['avg_risk'] or 7.0  # Default high risk
                sectors = [s for s in result[0]['sectors'] if s]
                dominant_sector = max(set(sectors), key=sectors.count) if sectors else None
            else:
                avg_risk = 7.0
                dominant_sector = None
            
            density = self._calculate_community_density(node_ids)
            
            return Community(
                id=community_id,
                nodes=node_ids,
                size=len(node_ids),
                density=density,
                avg_risk_score=avg_risk,
                dominant_sector=dominant_sector,
                risk_level=self._categorize_risk_level(avg_risk)
            )
            
        except Exception as e:
            logger.error(f"Error creating risk community: {e}")
            return Community(
                id=community_id,
                nodes=node_ids,
                size=len(node_ids),
                density=0.0,
                avg_risk_score=7.0,
                dominant_sector=None,
                risk_level="HIGH"
            )
    
    def _calculate_community_density(self, node_ids: List[str]) -> float:
        """커뮤니티 밀도 계산"""
        try:
            if len(node_ids) < 2:
                return 0.0
            
            query = """
            MATCH (n1) WHERE n1.id IN $node_ids
            MATCH (n2) WHERE n2.id IN $node_ids AND n1 <> n2
            OPTIONAL MATCH (n1)-[r]-(n2)
            
            WITH count(DISTINCT r) as edges, count(DISTINCT n1) as nodes
            RETURN 
                CASE 
                    WHEN nodes > 1 THEN (edges * 2.0) / (nodes * (nodes - 1))
                    ELSE 0.0 
                END as density
            """
            
            result = self.session.run_query(query, node_ids=node_ids)
            return result[0]['density'] if result else 0.0
            
        except:
            return 0.0
    
    def _calculate_modularity_approximation(self, communities: List[Community]) -> float:
        """모듈러리티 근사 계산"""
        # 간단한 모듈러리티 근사
        if not communities:
            return 0.0
        
        total_edges = sum(c.size * (c.size - 1) / 2 * c.density for c in communities)
        total_nodes = sum(c.size for c in communities)
        
        if total_nodes == 0:
            return 0.0
        
        # 정규화된 모듈러리티 근사값
        return min(total_edges / (total_nodes * total_nodes), 1.0)
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """리스크 레벨 분류"""
        if risk_score >= 7.0:
            return "HIGH"
        elif risk_score >= 5.0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_risk_recommendations(self, analysis: Dict) -> List[str]:
        """리스크 권장사항 생성"""
        recommendations = []
        
        risk_level = analysis.get('overall_risk_level', 'MEDIUM')
        community_size = analysis.get('community_size', 0)
        
        if risk_level == "HIGH":
            recommendations.append("즉시 리스크 완화 조치 필요")
            recommendations.append("커뮤니티 내 고위험 엔티티 모니터링 강화")
        
        if community_size > 10:
            recommendations.append("대규모 커뮤니티로 시스템적 리스크 주의")
        
        if analysis.get('risk_count', 0) > 5:
            recommendations.append("다양한 리스크 유형에 노출되어 종합적 대응 필요")
        
        return recommendations
    
    def _fallback_community_detection(
        self,
        node_types: Optional[List[str]],
        min_community_size: int
    ) -> CommunityAnalysisResult:
        """Graph Data Science가 없을 때 폴백 커뮤니티 탐지"""
        try:
            # 간단한 연결성 기반 커뮤니티 탐지
            node_filter = ""
            if node_types:
                labels_condition = " OR ".join([f"'{nt}' IN labels(n)" for nt in node_types])
                node_filter = f"WHERE {labels_condition}"
            
            query = f"""
            MATCH (n)-[r]-(m)
            {node_filter}
            WITH n, collect(DISTINCT m.id) as neighbors
            WHERE size(neighbors) >= {min_community_size - 1}
            
            RETURN 
                n.id as node_id,
                n.name as node_name,
                n.risk_score as risk_score,
                n.sector as sector,
                neighbors,
                size(neighbors) as degree
            ORDER BY degree DESC
            LIMIT 50
            """
            
            results = self.session.run_query(query)
            
            # 간단한 클러스터링 (가장 연결이 많은 노드들 기준)
            communities = []
            processed_nodes = set()
            
            for i, row in enumerate(results):
                if row['node_id'] not in processed_nodes:
                    # 간단한 커뮤니티 생성
                    community_nodes = [row['node_id']] + row['neighbors'][:10]  # 상위 10개 이웃
                    
                    community = Community(
                        id=i,
                        nodes=community_nodes,
                        size=len(community_nodes),
                        density=0.5,  # 추정값
                        avg_risk_score=row['risk_score'] or 5.0,
                        dominant_sector=row['sector'],
                        risk_level=self._categorize_risk_level(row['risk_score'] or 5.0)
                    )
                    
                    communities.append(community)
                    processed_nodes.update(community_nodes)
            
            return CommunityAnalysisResult(
                communities=communities,
                modularity=0.3,  # 추정값
                total_communities=len(communities),
                largest_community_size=max(c.size for c in communities) if communities else 0,
                avg_community_size=sum(c.size for c in communities) / len(communities) if communities else 0
            )
            
        except Exception as e:
            logger.error(f"Error in fallback community detection: {e}")
            return CommunityAnalysisResult(
                communities=[],
                modularity=0.0,
                total_communities=0,
                largest_community_size=0,
                avg_community_size=0.0
            )


# 싱글톤 인스턴스
community_detector = CommunityDetector()
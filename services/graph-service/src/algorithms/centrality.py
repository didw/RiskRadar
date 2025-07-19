"""중심성 분석 알고리즘"""
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from src.neo4j.session import session

logger = logging.getLogger(__name__)


@dataclass
class CentralityMetrics:
    """중심성 메트릭"""
    node_id: str
    node_type: str
    betweenness: float
    closeness: float
    degree: int
    eigenvector: float
    pagerank: float


class CentralityAnalyzer:
    """중심성 분석기"""
    
    def __init__(self):
        self.session = session
    
    def calculate_betweenness_centrality(
        self, 
        node_types: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[CentralityMetrics]:
        """매개 중심성 계산
        
        Args:
            node_types: 분석할 노드 타입 (None이면 모든 타입)
            limit: 결과 제한수
            
        Returns:
            중심성 메트릭 리스트
        """
        try:
            # Node types filter
            node_filter = ""
            if node_types:
                labels_condition = " OR ".join([f"'{nt}' IN labels(n)" for nt in node_types])
                node_filter = f"WHERE {labels_condition}"
            
            query = f"""
            CALL gds.graph.project(
                'centrality-graph',
                '*',
                '*'
            )
            YIELD graphName, nodeCount, relationshipCount
            
            CALL gds.betweenness.stream('centrality-graph')
            YIELD nodeId, score
            
            MATCH (n) WHERE id(n) = nodeId {node_filter}
            RETURN 
                n.id as node_id,
                labels(n)[0] as node_type,
                score as betweenness
            ORDER BY score DESC
            LIMIT {limit}
            """
            
            results = self.session.run_query(query)
            
            metrics = []
            for row in results:
                # Get additional metrics for each node
                degree = self._get_degree_centrality(row['node_id'])
                closeness = self._get_closeness_centrality(row['node_id'])
                eigenvector = self._get_eigenvector_centrality(row['node_id'])
                pagerank = self._get_pagerank_centrality(row['node_id'])
                
                metrics.append(CentralityMetrics(
                    node_id=row['node_id'],
                    node_type=row['node_type'],
                    betweenness=row['betweenness'],
                    closeness=closeness,
                    degree=degree,
                    eigenvector=eigenvector,
                    pagerank=pagerank
                ))
            
            # Clean up projected graph
            self.session.run_query("CALL gds.graph.drop('centrality-graph')")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating betweenness centrality: {e}")
            # Fallback to simple degree centrality
            return self._fallback_centrality_calculation(node_types, limit)
    
    def calculate_pagerank(
        self,
        damping_factor: float = 0.85,
        iterations: int = 20,
        tolerance: float = 0.0001,
        node_types: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Tuple[str, str, float]]:
        """PageRank 계산
        
        Args:
            damping_factor: 감쇠 인수 (0.0-1.0)
            iterations: 최대 반복 횟수
            tolerance: 수렴 허용 오차
            node_types: 분석할 노드 타입
            limit: 결과 제한수
            
        Returns:
            (node_id, node_type, pagerank_score) 튜플 리스트
        """
        try:
            # Create graph projection for PageRank
            projection_query = """
            CALL gds.graph.project(
                'pagerank-graph',
                '*',
                {
                    '*': {
                        orientation: 'UNDIRECTED'
                    }
                }
            )
            """
            self.session.run_query(projection_query)
            
            # Run PageRank algorithm
            pagerank_query = f"""
            CALL gds.pageRank.stream(
                'pagerank-graph',
                {{
                    dampingFactor: {damping_factor},
                    maxIterations: {iterations},
                    tolerance: {tolerance}
                }}
            )
            YIELD nodeId, score
            
            MATCH (n) WHERE id(n) = nodeId
            RETURN 
                n.id as node_id,
                labels(n)[0] as node_type,
                score as pagerank_score
            ORDER BY score DESC
            LIMIT {limit}
            """
            
            results = self.session.run_query(pagerank_query)
            
            # Clean up projected graph
            self.session.run_query("CALL gds.graph.drop('pagerank-graph')")
            
            return [(row['node_id'], row['node_type'], row['pagerank_score']) 
                   for row in results]
            
        except Exception as e:
            logger.error(f"Error calculating PageRank: {e}")
            return self._fallback_pagerank_calculation(node_types, limit)
    
    def find_influential_nodes(
        self,
        node_type: str = "Company",
        min_connections: int = 5,
        limit: int = 50
    ) -> List[Dict]:
        """영향력 있는 노드 찾기
        
        Args:
            node_type: 노드 타입
            min_connections: 최소 연결 수
            limit: 결과 제한수
            
        Returns:
            영향력 노드 정보 리스트
        """
        try:
            query = f"""
            MATCH (n:{node_type})
            OPTIONAL MATCH (n)-[r]-(connected)
            
            WITH n, count(DISTINCT connected) as connection_count,
                 avg(connected.risk_score) as avg_connected_risk,
                 collect(DISTINCT labels(connected)[0]) as connected_types
            
            WHERE connection_count >= {min_connections}
            
            RETURN 
                n.id as node_id,
                n.name as name,
                n.risk_score as risk_score,
                connection_count,
                avg_connected_risk,
                connected_types,
                (connection_count * 0.4 + 
                 COALESCE(n.risk_score, 5.0) * 0.3 +
                 COALESCE(avg_connected_risk, 5.0) * 0.3) as influence_score
            
            ORDER BY influence_score DESC
            LIMIT {limit}
            """
            
            results = self.session.run_query(query)
            
            influential_nodes = []
            for row in results:
                node_info = {
                    'id': row['node_id'],
                    'name': row['name'],
                    'type': node_type,
                    'risk_score': row['risk_score'],
                    'connection_count': row['connection_count'],
                    'avg_connected_risk': row['avg_connected_risk'],
                    'connected_types': row['connected_types'],
                    'influence_score': row['influence_score']
                }
                influential_nodes.append(node_info)
            
            return influential_nodes
            
        except Exception as e:
            logger.error(f"Error finding influential nodes: {e}")
            return []
    
    def analyze_risk_propagation(
        self,
        source_node_id: str,
        max_depth: int = 3,
        min_risk_threshold: float = 6.0
    ) -> Dict:
        """리스크 전파 분석
        
        Args:
            source_node_id: 시작 노드 ID
            max_depth: 최대 탐색 깊이
            min_risk_threshold: 최소 리스크 임계값
            
        Returns:
            리스크 전파 분석 결과
        """
        try:
            query = f"""
            MATCH (source {{id: $source_id}})
            
            // Find risk propagation paths
            MATCH path = (source)-[*1..{max_depth}]-(target)
            WHERE target.risk_score >= {min_risk_threshold}
            
            WITH source, target, path,
                 length(path) as path_length,
                 reduce(risk = 0.0, n in nodes(path) | 
                   risk + COALESCE(n.risk_score, 5.0)) / length(path) as avg_path_risk
            
            // Calculate risk propagation score
            WITH source, target, path, path_length, avg_path_risk,
                 (target.risk_score * (1.0 / path_length) * 
                  (avg_path_risk / 10.0)) as propagation_score
            
            RETURN 
                source.id as source_id,
                source.name as source_name,
                collect({{
                    target_id: target.id,
                    target_name: target.name,
                    target_risk: target.risk_score,
                    path_length: path_length,
                    avg_path_risk: avg_path_risk,
                    propagation_score: propagation_score
                }}) as risk_paths,
                avg(propagation_score) as overall_propagation_risk,
                count(DISTINCT target) as affected_entities
            """
            
            result = self.session.run_query(query, source_id=source_node_id)
            
            if not result:
                return {
                    'source_id': source_node_id,
                    'risk_paths': [],
                    'overall_propagation_risk': 0.0,
                    'affected_entities': 0
                }
            
            data = result[0]
            
            # Sort risk paths by propagation score
            risk_paths = sorted(
                data['risk_paths'],
                key=lambda x: x['propagation_score'],
                reverse=True
            )
            
            return {
                'source_id': data['source_id'],
                'source_name': data['source_name'],
                'risk_paths': risk_paths[:20],  # Top 20 paths
                'overall_propagation_risk': data['overall_propagation_risk'],
                'affected_entities': data['affected_entities']
            }
            
        except Exception as e:
            logger.error(f"Error analyzing risk propagation: {e}")
            return {
                'source_id': source_node_id,
                'risk_paths': [],
                'overall_propagation_risk': 0.0,
                'affected_entities': 0,
                'error': str(e)
            }
    
    def _get_degree_centrality(self, node_id: str) -> int:
        """단순 연결 중심성 계산"""
        try:
            query = """
            MATCH (n {id: $node_id})-[r]-()
            RETURN count(r) as degree
            """
            result = self.session.run_query(query, node_id=node_id)
            return result[0]['degree'] if result else 0
        except:
            return 0
    
    def _get_closeness_centrality(self, node_id: str) -> float:
        """근접 중심성 계산 (근사치)"""
        try:
            query = """
            MATCH (n {id: $node_id})
            MATCH path = shortestPath((n)-[*..4]-(other))
            WHERE n <> other
            WITH n, avg(length(path)) as avg_distance, count(other) as reachable_nodes
            RETURN CASE 
                WHEN avg_distance > 0 THEN reachable_nodes / avg_distance 
                ELSE 0.0 
            END as closeness
            """
            result = self.session.run_query(query, node_id=node_id)
            return result[0]['closeness'] if result else 0.0
        except:
            return 0.0
    
    def _get_eigenvector_centrality(self, node_id: str) -> float:
        """고유벡터 중심성 계산 (근사치)"""
        try:
            # 간단한 근사: 연결된 노드들의 연결도 평균
            query = """
            MATCH (n {id: $node_id})-[r]-(neighbor)
            OPTIONAL MATCH (neighbor)-[r2]-()
            WITH n, neighbor, count(r2) as neighbor_degree
            RETURN avg(neighbor_degree) as eigenvector_approx
            """
            result = self.session.run_query(query, node_id=node_id)
            return (result[0]['eigenvector_approx'] or 0.0) / 100.0  # 정규화
        except:
            return 0.0
    
    def _get_pagerank_centrality(self, node_id: str) -> float:
        """PageRank 중심성 계산 (근사치)"""
        try:
            # 간단한 근사: 연결도 기반
            degree = self._get_degree_centrality(node_id)
            return min(degree / 50.0, 1.0)  # 0-1로 정규화
        except:
            return 0.0
    
    def _fallback_centrality_calculation(
        self, 
        node_types: Optional[List[str]], 
        limit: int
    ) -> List[CentralityMetrics]:
        """Graph Data Science가 없을 때 폴백 계산"""
        try:
            node_filter = ""
            if node_types:
                labels_condition = " OR ".join([f"'{nt}' IN labels(n)" for nt in node_types])
                node_filter = f"WHERE {labels_condition}"
            
            query = f"""
            MATCH (n)-[r]-()
            {node_filter}
            WITH n, count(r) as degree
            RETURN 
                n.id as node_id,
                labels(n)[0] as node_type,
                degree,
                degree * 0.1 as betweenness_approx
            ORDER BY degree DESC
            LIMIT {limit}
            """
            
            results = self.session.run_query(query)
            
            metrics = []
            for row in results:
                metrics.append(CentralityMetrics(
                    node_id=row['node_id'],
                    node_type=row['node_type'],
                    betweenness=row['betweenness_approx'],
                    closeness=0.0,
                    degree=row['degree'],
                    eigenvector=0.0,
                    pagerank=min(row['degree'] / 50.0, 1.0)
                ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in fallback centrality calculation: {e}")
            return []
    
    def _fallback_pagerank_calculation(
        self,
        node_types: Optional[List[str]],
        limit: int
    ) -> List[Tuple[str, str, float]]:
        """PageRank 폴백 계산"""
        try:
            node_filter = ""
            if node_types:
                labels_condition = " OR ".join([f"'{nt}' IN labels(n)" for nt in node_types])
                node_filter = f"WHERE {labels_condition}"
            
            query = f"""
            MATCH (n)-[r]-()
            {node_filter}
            WITH n, count(r) as degree
            RETURN 
                n.id as node_id,
                labels(n)[0] as node_type,
                (degree * 1.0 / 50.0) as pagerank_approx
            ORDER BY degree DESC
            LIMIT {limit}
            """
            
            results = self.session.run_query(query)
            
            return [(row['node_id'], row['node_type'], 
                    min(row['pagerank_approx'], 1.0)) for row in results]
            
        except Exception as e:
            logger.error(f"Error in fallback PageRank calculation: {e}")
            return []


# 싱글톤 인스턴스
centrality_analyzer = CentralityAnalyzer()
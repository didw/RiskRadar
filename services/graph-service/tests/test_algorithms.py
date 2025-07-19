"""고급 그래프 알고리즘 테스트"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import os

# Mock Neo4j environment
os.environ["NEO4J_URI"] = "bolt://mock:7687"
os.environ["NEO4J_USER"] = "mock"
os.environ["NEO4J_PASSWORD"] = "mock"


class TestCentralityAnalyzer:
    """중심성 분석기 테스트"""
    
    @patch('src.neo4j.session.session')
    def test_betweenness_centrality_calculation(self, mock_session):
        """매개 중심성 계산 테스트"""
        from src.algorithms.centrality import centrality_analyzer
        
        # Mock 데이터 설정
        mock_session.run_query.side_effect = [
            # 첫 번째 호출: 메인 쿼리
            [
                {
                    'node_id': 'company-1',
                    'node_type': 'Company',
                    'betweenness': 0.8
                },
                {
                    'node_id': 'company-2', 
                    'node_type': 'Company',
                    'betweenness': 0.6
                }
            ],
            # 후속 호출들: 개별 중심성 메트릭
            [{'degree': 10}],  # degree for company-1
            [{'closeness': 0.7}],  # closeness for company-1
            [{'eigenvector_approx': 15.0}],  # eigenvector for company-1
            [{'degree': 8}],  # degree for company-2
            [{'closeness': 0.5}],  # closeness for company-2
            [{'eigenvector_approx': 12.0}],  # eigenvector for company-2
            []  # cleanup query
        ]
        
        # 중심성 계산 실행
        metrics = centrality_analyzer.calculate_betweenness_centrality(
            node_types=['Company'],
            limit=10
        )
        
        # 결과 검증
        assert len(metrics) == 2
        assert metrics[0].node_id == 'company-1'
        assert metrics[0].betweenness == 0.8
        assert metrics[0].degree == 10
        assert metrics[1].node_id == 'company-2'
        assert metrics[1].betweenness == 0.6
        
        print("✅ Betweenness centrality calculation test passed")
    
    @patch('src.neo4j.session.session')
    def test_pagerank_calculation(self, mock_session):
        """PageRank 계산 테스트"""
        from src.algorithms.centrality import centrality_analyzer
        
        # Mock 데이터 설정
        mock_session.run_query.side_effect = [
            [],  # projection query
            [
                {
                    'node_id': 'company-1',
                    'node_type': 'Company',
                    'pagerank_score': 0.25
                },
                {
                    'node_id': 'person-1',
                    'node_type': 'Person', 
                    'pagerank_score': 0.15
                }
            ],
            []  # cleanup query
        ]
        
        # PageRank 계산 실행
        results = centrality_analyzer.calculate_pagerank(
            damping_factor=0.85,
            iterations=20,
            limit=10
        )
        
        # 결과 검증
        assert len(results) == 2
        assert results[0] == ('company-1', 'Company', 0.25)
        assert results[1] == ('person-1', 'Person', 0.15)
        
        print("✅ PageRank calculation test passed")
    
    @patch('src.neo4j.session.session')
    def test_influential_nodes_detection(self, mock_session):
        """영향력 있는 노드 탐지 테스트"""
        from src.algorithms.centrality import centrality_analyzer
        
        # Mock 데이터 설정
        mock_session.run_query.return_value = [
            {
                'node_id': 'company-1',
                'name': 'Apple Inc.',
                'risk_score': 3.5,
                'connection_count': 25,
                'avg_connected_risk': 4.2,
                'connected_types': ['Company', 'Person', 'Event'],
                'influence_score': 8.7
            }
        ]
        
        # 영향력 노드 탐지 실행
        influential = centrality_analyzer.find_influential_nodes(
            node_type='Company',
            min_connections=5
        )
        
        # 결과 검증
        assert len(influential) == 1
        node = influential[0]
        assert node['id'] == 'company-1'
        assert node['name'] == 'Apple Inc.'
        assert node['connection_count'] == 25
        assert node['influence_score'] == 8.7
        
        print("✅ Influential nodes detection test passed")
    
    @patch('src.neo4j.session.session')
    def test_risk_propagation_analysis(self, mock_session):
        """리스크 전파 분석 테스트"""
        from src.algorithms.centrality import centrality_analyzer
        
        # Mock 데이터 설정
        mock_session.run_query.return_value = [
            {
                'source_id': 'company-1',
                'source_name': 'Apple Inc.',
                'risk_paths': [
                    {
                        'target_id': 'company-2',
                        'target_name': 'Samsung',
                        'target_risk': 7.5,
                        'path_length': 2,
                        'avg_path_risk': 6.8,
                        'propagation_score': 4.2
                    }
                ],
                'overall_propagation_risk': 4.2,
                'affected_entities': 5
            }
        ]
        
        # 리스크 전파 분석 실행
        result = centrality_analyzer.analyze_risk_propagation(
            source_node_id='company-1',
            max_depth=3,
            min_risk_threshold=6.0
        )
        
        # 결과 검증
        assert result['source_id'] == 'company-1'
        assert result['source_name'] == 'Apple Inc.'
        assert result['affected_entities'] == 5
        assert len(result['risk_paths']) == 1
        assert result['risk_paths'][0]['target_id'] == 'company-2'
        
        print("✅ Risk propagation analysis test passed")


class TestCommunityDetector:
    """커뮤니티 탐지기 테스트"""
    
    @patch('src.neo4j.session.session')
    def test_louvain_community_detection(self, mock_session):
        """Louvain 커뮤니티 탐지 테스트"""
        from src.algorithms.community import community_detector
        
        # Mock 데이터 설정
        mock_session.run_query.side_effect = [
            [],  # projection query
            [
                {
                    'node_id': 'company-1',
                    'node_name': 'Apple Inc.',
                    'node_type': 'Company',
                    'risk_score': 3.5,
                    'sector': 'Technology',
                    'communityId': 0
                },
                {
                    'node_id': 'company-2',
                    'node_name': 'Microsoft',
                    'node_type': 'Company',
                    'risk_score': 4.0,
                    'sector': 'Technology',
                    'communityId': 0
                },
                {
                    'node_id': 'company-3',
                    'node_name': 'Goldman Sachs',
                    'node_type': 'Company',
                    'risk_score': 6.5,
                    'sector': 'Finance',
                    'communityId': 1
                }
            ],
            [],  # cleanup query
            [{'density': 0.6}],  # density calculation for community 0
            [{'density': 0.4}]   # density calculation for community 1
        ]
        
        # 커뮤니티 탐지 실행
        result = community_detector.detect_communities_louvain(
            node_types=['Company'],
            min_community_size=2
        )
        
        # 결과 검증
        assert result.total_communities == 2
        assert len(result.communities) == 2
        
        tech_community = next(c for c in result.communities if c.dominant_sector == 'Technology')
        assert tech_community.size == 2
        assert 'company-1' in tech_community.nodes
        assert 'company-2' in tech_community.nodes
        
        print("✅ Louvain community detection test passed")
    
    @patch('src.neo4j.session.session')
    def test_risk_communities_detection(self, mock_session):
        """리스크 커뮤니티 탐지 테스트"""
        from src.algorithms.community import community_detector
        
        # Mock 데이터 설정
        mock_session.run_query.side_effect = [
            # 고위험 노드 조회
            [
                {'node_id': 'company-1', 'risk_score': 7.5},
                {'node_id': 'company-2', 'risk_score': 8.0}
            ],
            # 연결 컴포넌트 조회
            [{'component_nodes': ['company-2', 'company-3']}],
            # 커뮤니티 세부 정보
            [{'avg_risk': 7.8, 'sectors': ['Finance', 'Technology']}],
            [{'density': 0.7}]
        ]
        
        # 리스크 커뮤니티 탐지 실행
        communities = community_detector.detect_risk_communities(
            min_risk_threshold=7.0,
            min_community_size=2
        )
        
        # 결과 검증
        assert len(communities) == 1
        community = communities[0]
        assert community.size >= 2
        assert community.risk_level == "HIGH"
        assert community.avg_risk_score >= 7.0
        
        print("✅ Risk communities detection test passed")
    
    @patch('src.neo4j.session.session')
    def test_sector_clusters_finding(self, mock_session):
        """섹터 클러스터 찾기 테스트"""
        from src.algorithms.community import community_detector
        
        # Mock 데이터 설정
        mock_session.run_query.return_value = [
            {
                'center_id': 'company-1',
                'center_name': 'Apple Inc.',
                'center_risk': 3.5,
                'connected_ids': ['company-2', 'company-3', 'company-4'],
                'cluster_size': 3
            }
        ]
        
        # 섹터 클러스터 찾기 실행
        clusters = community_detector.find_sector_clusters(
            sector='Technology',
            min_cluster_size=3
        )
        
        # 결과 검증
        assert len(clusters) == 1
        cluster = clusters[0]
        assert cluster['center_id'] == 'company-1'
        assert cluster['sector'] == 'Technology'
        assert cluster['cluster_size'] == 3
        
        print("✅ Sector clusters finding test passed")


class TestPathFinder:
    """경로 탐색기 테스트"""
    
    @patch('src.neo4j.session.session')
    def test_shortest_paths_finding(self, mock_session):
        """최단 경로 찾기 테스트"""
        from src.algorithms.pathfinding import pathfinder
        
        # Mock 데이터 설정
        mock_session.run_query.return_value = [
            {
                'nodes': [
                    {
                        'id': 'company-1',
                        'name': 'Apple Inc.',
                        'type': 'Company',
                        'risk_score': 3.5,
                        'properties': {'sector': 'Technology'}
                    },
                    {
                        'id': 'person-1', 
                        'name': 'Tim Cook',
                        'type': 'Person',
                        'risk_score': 5.0,
                        'properties': {'role': 'CEO'}
                    }
                ],
                'relationships': [
                    {
                        'type': 'WORKS_AT',
                        'properties': {},
                        'strength': 0.9,
                        'confidence': 0.95
                    }
                ],
                'path_length': 1
            }
        ]
        
        # 최단 경로 찾기 실행
        paths = pathfinder.find_shortest_paths(
            source_id='company-1',
            target_id='person-1',
            max_length=3
        )
        
        # 결과 검증
        assert len(paths) == 1
        path = paths[0]
        assert path.total_length == 1
        assert len(path.nodes) == 2
        assert path.nodes[0].id == 'company-1'
        assert path.nodes[1].id == 'person-1'
        assert len(path.relationships) == 1
        assert path.relationships[0].type == 'WORKS_AT'
        
        print("✅ Shortest paths finding test passed")
    
    @patch('src.neo4j.session.session')
    def test_risk_propagation_paths(self, mock_session):
        """리스크 전파 경로 테스트"""
        from src.algorithms.pathfinding import pathfinder
        
        # Mock 데이터 설정
        mock_session.run_query.return_value = [
            {
                'nodes': [
                    {
                        'id': 'company-1',
                        'name': 'Source Company',
                        'type': 'Company',
                        'risk_score': 8.0,
                        'properties': {}
                    },
                    {
                        'id': 'company-2',
                        'name': 'Target Company',
                        'type': 'Company',
                        'risk_score': 7.5,
                        'properties': {}
                    }
                ],
                'relationships': [
                    {
                        'type': 'COMPETES_WITH',
                        'properties': {},
                        'strength': 0.8,
                        'confidence': 0.9
                    }
                ],
                'path_length': 1,
                'total_path_risk': 15.5,
                'avg_path_risk': 7.75
            }
        ]
        
        # 리스크 전파 경로 찾기 실행
        paths = pathfinder.find_risk_propagation_paths(
            source_id='company-1',
            min_risk_threshold=7.0,
            max_depth=3
        )
        
        # 결과 검증
        assert len(paths) == 1
        path = paths[0]
        assert path.path_type == "CASCADING"
        assert path.risk_score == 7.75
        assert len(path.risk_factors) > 0  # Should have high-risk factors
        
        print("✅ Risk propagation paths test passed")
    
    @patch('src.neo4j.session.session')
    def test_bottleneck_nodes_analysis(self, mock_session):
        """병목 노드 분석 테스트"""
        from src.algorithms.pathfinding import pathfinder
        
        # Mock 데이터 설정
        mock_session.run_query.return_value = [
            {
                'node_id': 'company-1',
                'node_name': 'Central Hub Company',
                'node_type': 'Company',
                'risk_score': 4.5,
                'path_count': 25,
                'degree': 15,
                'bottleneck_score': 21.0
            }
        ]
        
        # 병목 노드 분석 실행
        bottlenecks = pathfinder.analyze_bottleneck_nodes(
            node_types=['Company'],
            min_path_count=5
        )
        
        # 결과 검증
        assert len(bottlenecks) == 1
        bottleneck = bottlenecks[0]
        assert bottleneck['node_id'] == 'company-1'
        assert bottleneck['path_count'] == 25
        assert bottleneck['degree'] == 15
        assert bottleneck['criticality'] == 'HIGH'
        
        print("✅ Bottleneck nodes analysis test passed")
    
    @patch('src.neo4j.session.session')
    def test_path_resilience_calculation(self, mock_session):
        """경로 복원력 계산 테스트"""
        from src.algorithms.pathfinding import pathfinder
        
        # Mock 데이터 설정 (여러 호출에 대응)
        mock_session.run_query.side_effect = [
            # find_shortest_paths 호출
            [
                {
                    'nodes': [
                        {'id': 'A', 'name': 'A', 'type': 'Company', 'risk_score': 3.0, 'properties': {}},
                        {'id': 'B', 'name': 'B', 'type': 'Company', 'risk_score': 4.0, 'properties': {}},
                        {'id': 'C', 'name': 'C', 'type': 'Company', 'risk_score': 5.0, 'properties': {}}
                    ],
                    'relationships': [
                        {'type': 'CONNECTS', 'properties': {}, 'strength': 0.8, 'confidence': 0.9},
                        {'type': 'CONNECTS', 'properties': {}, 'strength': 0.7, 'confidence': 0.8}
                    ],
                    'path_length': 2
                }
            ]
        ]
        
        # 경로 복원력 계산 실행
        result = pathfinder.calculate_path_resilience(
            source_id='A',
            target_id='C'
        )
        
        # 결과 검증
        assert 'resilience_score' in result
        assert 'path_diversity' in result
        assert 'failure_impact' in result
        assert 'recommendations' in result
        assert result['total_paths'] == 1
        
        print("✅ Path resilience calculation test passed")


if __name__ == "__main__":
    # 중심성 분석기 테스트
    test_centrality = TestCentralityAnalyzer()
    test_centrality.test_betweenness_centrality_calculation()
    test_centrality.test_pagerank_calculation()
    test_centrality.test_influential_nodes_detection()
    test_centrality.test_risk_propagation_analysis()
    
    # 커뮤니티 탐지기 테스트
    test_community = TestCommunityDetector()
    test_community.test_louvain_community_detection()
    test_community.test_risk_communities_detection()
    test_community.test_sector_clusters_finding()
    
    # 경로 탐색기 테스트
    test_pathfinder = TestPathFinder()
    test_pathfinder.test_shortest_paths_finding()
    test_pathfinder.test_risk_propagation_paths()
    test_pathfinder.test_bottleneck_nodes_analysis()
    test_pathfinder.test_path_resilience_calculation()
    
    print("\n🎉 All advanced graph algorithms tests passed!")
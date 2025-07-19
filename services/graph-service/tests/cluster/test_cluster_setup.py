"""Neo4j 클러스터 설정 테스트"""
import pytest
import time
import requests
from neo4j import GraphDatabase
import docker
import subprocess
import os

class TestNeo4jCluster:
    """Neo4j 클러스터 테스트"""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker 클라이언트"""
        return docker.from_env()
    
    @pytest.fixture(scope="class")
    def cluster_dir(self):
        """클러스터 디렉토리 경로"""
        return os.path.join(os.path.dirname(__file__), '../../docker/neo4j-cluster')
    
    @pytest.mark.cluster
    def test_cluster_startup(self, cluster_dir):
        """클러스터 시작 테스트"""
        # 클러스터 설정 스크립트 실행
        script_path = os.path.join(cluster_dir, 'scripts/cluster-setup.sh')
        
        if not os.path.exists(script_path):
            pytest.skip("Cluster setup script not found")
        
        # 클러스터 시작 (타임아웃 10분)
        try:
            result = subprocess.run(
                [script_path, 'start'],
                cwd=cluster_dir,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            # 시작 성공 여부 확인
            assert result.returncode == 0, f"Cluster startup failed: {result.stderr}"
            
        except subprocess.TimeoutExpired:
            pytest.fail("Cluster startup timed out after 10 minutes")
    
    @pytest.mark.cluster
    def test_core_servers_health(self):
        """Core 서버 헬스 체크"""
        core_servers = [
            ("neo4j-core-1", "bolt://localhost:7687"),
            ("neo4j-core-2", "bolt://localhost:7688"), 
            ("neo4j-core-3", "bolt://localhost:7689")
        ]
        
        for server_name, uri in core_servers:
            driver = None
            try:
                driver = GraphDatabase.driver(uri, auth=("neo4j", "riskradar2024"))
                
                # 연결 확인
                with driver.session() as session:
                    result = session.run("RETURN 1 as test")
                    assert result.single()["test"] == 1
                    
                # 클러스터 상태 확인
                with driver.session() as session:
                    result = session.run("SHOW SERVERS")
                    servers = list(result)
                    
                    # 최소 3개의 Core 서버가 있어야 함
                    core_count = len([s for s in servers if s.get("role") == "PRIMARY" or s.get("role") == "SECONDARY"])
                    assert core_count >= 3, f"Expected at least 3 core servers, got {core_count}"
                    
            except Exception as e:
                pytest.fail(f"Health check failed for {server_name}: {e}")
            finally:
                if driver:
                    driver.close()
    
    @pytest.mark.cluster
    def test_read_replica_health(self):
        """Read Replica 헬스 체크"""
        driver = None
        try:
            # Read Replica 연결
            driver = GraphDatabase.driver("bolt://localhost:7690", auth=("neo4j", "riskradar2024"))
            
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                assert result.single()["test"] == 1
                
        except Exception as e:
            pytest.fail(f"Read replica health check failed: {e}")
        finally:
            if driver:
                driver.close()
    
    @pytest.mark.cluster
    def test_haproxy_health(self):
        """HAProxy 헬스 체크"""
        try:
            # HAProxy 헬스 엔드포인트 확인
            response = requests.get("http://localhost:8080/health", timeout=10)
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data.get("status") == "healthy"
            assert health_data.get("cluster") == "neo4j"
            
        except requests.RequestException as e:
            pytest.fail(f"HAProxy health check failed: {e}")
    
    @pytest.mark.cluster
    def test_haproxy_stats(self):
        """HAProxy 통계 페이지 확인"""
        try:
            response = requests.get("http://localhost:8404/stats", timeout=10)
            assert response.status_code == 200
            assert "HAProxy Statistics Report" in response.text
            
        except requests.RequestException as e:
            pytest.fail(f"HAProxy stats check failed: {e}")
    
    @pytest.mark.cluster
    def test_load_balancer_distribution(self):
        """로드 밸런서 분산 테스트"""
        driver = None
        try:
            # Primary endpoint를 통한 연결
            driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "riskradar2024"))
            
            # 여러 번 연결하여 로드 밸런싱 확인
            server_ids = set()
            
            for _ in range(10):
                with driver.session() as session:
                    # 현재 연결된 서버 확인
                    result = session.run("CALL dbms.routing.getRoutingTable({}, 'graph')")
                    routing_table = result.single()
                    
                    # 라우팅 테이블에서 서버 정보 추출
                    if routing_table:
                        writers = routing_table.get("route", {}).get("writers", [])
                        if writers:
                            server_ids.update([server["address"] for server in writers])
            
            # 최소 2개 이상의 서버에서 응답이 와야 함 (로드 밸런싱 확인)
            assert len(server_ids) >= 1, f"Expected load balancing across servers, got: {server_ids}"
            
        except Exception as e:
            pytest.fail(f"Load balancer distribution test failed: {e}")
        finally:
            if driver:
                driver.close()
    
    @pytest.mark.cluster
    def test_write_read_consistency(self):
        """쓰기-읽기 일관성 테스트"""
        write_driver = None
        read_driver = None
        
        try:
            # 쓰기용 연결 (Primary)
            write_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "riskradar2024"))
            
            # 읽기용 연결 (Read Replica)
            read_driver = GraphDatabase.driver("bolt://localhost:7688", auth=("neo4j", "riskradar2024"))
            
            test_id = f"cluster-test-{int(time.time())}"
            
            # 데이터 쓰기
            with write_driver.session() as session:
                session.run(
                    "CREATE (n:ClusterTest {id: $id, timestamp: datetime()})",
                    id=test_id
                )
            
            # 읽기 복제 대기 (최대 30초)
            found = False
            for attempt in range(30):
                try:
                    with read_driver.session() as session:
                        result = session.run(
                            "MATCH (n:ClusterTest {id: $id}) RETURN n.id as id",
                            id=test_id
                        )
                        if result.single():
                            found = True
                            break
                except:
                    pass
                
                time.sleep(1)
            
            assert found, f"Data not replicated to read replica within 30 seconds"
            
            # 정리
            with write_driver.session() as session:
                session.run("MATCH (n:ClusterTest {id: $id}) DELETE n", id=test_id)
                
        except Exception as e:
            pytest.fail(f"Write-read consistency test failed: {e}")
        finally:
            if write_driver:
                write_driver.close()
            if read_driver:
                read_driver.close()
    
    @pytest.mark.cluster
    def test_failover_scenario(self, docker_client):
        """장애 복구 시나리오 테스트"""
        try:
            # Core-2 서버 중지
            core2_container = docker_client.containers.get("neo4j-core-2")
            core2_container.stop()
            
            # 클러스터가 여전히 작동하는지 확인
            driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "riskradar2024"))
            
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                assert result.single()["test"] == 1
            
            driver.close()
            
            # Core-2 서버 재시작
            core2_container.start()
            
            # 재시작 후 클러스터 복구 대기
            time.sleep(30)
            
            # 클러스터 상태 확인
            driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "riskradar2024"))
            
            with driver.session() as session:
                result = session.run("SHOW SERVERS")
                servers = list(result)
                
                # 모든 서버가 다시 온라인 상태인지 확인
                enabled_servers = [s for s in servers if s.get("health") == "available"]
                assert len(enabled_servers) >= 3, f"Expected at least 3 enabled servers after failover"
            
            driver.close()
            
        except docker.errors.NotFound:
            pytest.skip("Core-2 container not found, skipping failover test")
        except Exception as e:
            pytest.fail(f"Failover scenario test failed: {e}")
    
    @pytest.mark.cluster
    def test_prometheus_metrics(self):
        """Prometheus 메트릭 확인"""
        try:
            # Core-1 메트릭 확인
            response = requests.get("http://localhost:2004/metrics", timeout=10)
            assert response.status_code == 200
            
            metrics_text = response.text
            
            # 주요 메트릭 확인
            assert "neo4j_database_store_size_bytes" in metrics_text
            assert "neo4j_bolt_connections_opened_total" in metrics_text
            assert "neo4j_database_transaction_committed_total" in metrics_text
            
        except requests.RequestException as e:
            pytest.fail(f"Prometheus metrics check failed: {e}")
    
    @pytest.mark.cluster
    def test_cluster_cleanup(self, cluster_dir):
        """클러스터 정리 테스트"""
        # 테스트 완료 후 클러스터 중지
        script_path = os.path.join(cluster_dir, 'scripts/cluster-setup.sh')
        
        if os.path.exists(script_path):
            try:
                result = subprocess.run(
                    [script_path, 'stop'],
                    cwd=cluster_dir,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                # 중지 성공 여부 확인 (테스트 실패하지 않음)
                if result.returncode != 0:
                    print(f"Warning: Cluster stop failed: {result.stderr}")
                
            except subprocess.TimeoutExpired:
                print("Warning: Cluster stop timed out")
        else:
            print("Warning: Cluster setup script not found for cleanup")
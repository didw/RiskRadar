"""
부하 테스트 스크립트
Sprint 1 요구사항: 동시 100 쿼리 처리, Write TPS > 100 달성 검증
"""
import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import sys
import os
import concurrent.futures
from threading import Thread

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.neo4j.driver import driver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """부하 테스트 결과"""
    test_name: str
    concurrent_users: int
    total_requests: int
    duration_seconds: float
    requests_per_second: float
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    max_response_time_ms: float
    min_response_time_ms: float
    errors: List[str]
    goal_achieved: bool


class GraphServiceLoadTest:
    """Graph Service 부하 테스트"""
    
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        self.test_company_ids = []
        self.results: List[LoadTestResult] = []
        
    async def setup_test_data(self):
        """테스트 데이터 설정"""
        try:
            # 기존 회사 ID 조회
            query = "MATCH (c:Company) RETURN c.id as id LIMIT 20"
            results = driver.execute_read(query)
            self.test_company_ids = [row["id"] for row in results if row["id"]]
            
            # 충분한 테스트 데이터가 없으면 생성
            if len(self.test_company_ids) < 10:
                await self._create_load_test_data()
                results = driver.execute_read(query)
                self.test_company_ids = [row["id"] for row in results if row["id"]]
            
            logger.info(f"Using {len(self.test_company_ids)} companies for load testing")
            
        except Exception as e:
            logger.error(f"Error setting up test data: {e}")
            # 폴백: 더미 ID 사용
            self.test_company_ids = [f"load-test-company-{i}" for i in range(20)]
    
    async def _create_load_test_data(self):
        """부하 테스트용 데이터 생성"""
        logger.info("Creating load test data...")
        
        # 100개 기업 생성
        batch_size = 10
        for batch in range(0, 100, batch_size):
            companies = []
            for i in range(batch, min(batch + batch_size, 100)):
                companies.append({
                    "id": f"load-test-company-{i}",
                    "name": f"Load Test Company {i}",
                    "sector": ["Technology", "Finance", "Healthcare", "Energy", "Retail"][i % 5],
                    "risk_score": 3.0 + (i % 8),  # 3.0 ~ 10.0
                    "market_cap": 100000000 + (i * 50000000),  # 다양한 시가총액
                    "created_at": int(time.time())
                })
            
            # 배치 생성
            query = """
            UNWIND $companies as company
            CREATE (c:Company {
                id: company.id,
                name: company.name,
                sector: company.sector,
                risk_score: company.risk_score,
                market_cap: company.market_cap,
                created_at: company.created_at
            })
            """
            
            try:
                driver.execute_write(query, companies=companies)
            except Exception as e:
                logger.debug(f"Batch creation failed (may already exist): {e}")
        
        # 관계 생성 (연결된 네트워크 구성)
        logger.info("Creating relationships for load test...")
        
        for i in range(0, 90, 10):
            relationships = []
            for j in range(i, i + 10):
                if j + 1 < 100:
                    relationships.append({
                        "from_id": f"load-test-company-{j}",
                        "to_id": f"load-test-company-{j + 1}",
                        "strength": 0.5 + (j % 5) * 0.1
                    })
            
            rel_query = """
            UNWIND $rels as rel
            MATCH (c1:Company {id: rel.from_id})
            MATCH (c2:Company {id: rel.to_id})
            CREATE (c1)-[:CONNECTED_TO {strength: rel.strength, created_at: timestamp()}]->(c2)
            """
            
            try:
                driver.execute_write(rel_query, rels=relationships)
            except Exception as e:
                logger.debug(f"Relationship creation failed: {e}")
    
    async def _make_http_request(self, session: aiohttp.ClientSession, 
                                url: str, method: str = "GET", 
                                json_data: Dict = None) -> Dict[str, Any]:
        """HTTP 요청 실행"""
        start_time = time.time()
        
        try:
            if method == "GET":
                async with session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "response_time_ms": response_time,
                        "status": response.status,
                        "data": result,
                        "error": None
                    }
            elif method == "POST":
                async with session.post(url, json=json_data) as response:
                    response_time = (time.time() - start_time) * 1000
                    result = await response.json()
                    return {
                        "success": response.status == 200,
                        "response_time_ms": response_time,
                        "status": response.status,
                        "data": result,
                        "error": None
                    }
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "response_time_ms": response_time,
                "status": 0,
                "data": None,
                "error": str(e)
            }
    
    async def concurrent_read_test(self, concurrent_users: int = 100, 
                                 duration_seconds: int = 60) -> LoadTestResult:
        """동시 읽기 요청 테스트"""
        logger.info(f"Running concurrent read test: {concurrent_users} users for {duration_seconds}s")
        
        results = []
        errors = []
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # 동시 사용자 시뮬레이션
            for user_id in range(concurrent_users):
                task = asyncio.create_task(
                    self._simulate_user_read_activity(session, user_id, end_time, results, errors)
                )
                tasks.append(task)
            
            # 모든 태스크 완료 대기
            await asyncio.gather(*tasks)
        
        actual_duration = time.time() - start_time
        
        # 결과 분석
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if successful_requests:
            response_times = [r["response_time_ms"] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)]
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
            max_response_time = min_response_time = 0
        
        rps = len(results) / actual_duration
        success_rate = len(successful_requests) / len(results) * 100 if results else 0
        
        return LoadTestResult(
            test_name="Concurrent Read Test",
            concurrent_users=concurrent_users,
            total_requests=len(results),
            duration_seconds=actual_duration,
            requests_per_second=rps,
            successful_requests=len(successful_requests),
            failed_requests=len(failed_requests),
            success_rate=success_rate,
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            max_response_time_ms=max_response_time,
            min_response_time_ms=min_response_time,
            errors=errors[:10],  # 최대 10개 에러만 기록
            goal_achieved=rps >= 50 and success_rate >= 95  # 목표: 50 RPS, 95% 성공률
        )
    
    async def _simulate_user_read_activity(self, session: aiohttp.ClientSession, 
                                         user_id: int, end_time: float,
                                         results: List, errors: List):
        """사용자 읽기 활동 시뮬레이션"""
        request_count = 0
        
        while time.time() < end_time:
            try:
                # 다양한 API 엔드포인트 호출
                company_id = self.test_company_ids[request_count % len(self.test_company_ids)]
                
                endpoints = [
                    f"{self.base_url}/api/v1/graph/optimized/company/{company_id}",
                    f"{self.base_url}/api/v1/graph/optimized/company/{company_id}/connections",
                    f"{self.base_url}/api/v1/graph/optimized/company/{company_id}/network-risk",
                    f"{self.base_url}/api/v1/graph/stats"
                ]
                
                endpoint = endpoints[request_count % len(endpoints)]
                result = await self._make_http_request(session, endpoint)
                results.append(result)
                
                if not result["success"]:
                    errors.append(f"User {user_id}: {result['error']}")
                
                request_count += 1
                
                # 사용자 간 요청 간격 (100-300ms)
                await asyncio.sleep(0.1 + (user_id % 3) * 0.1)
                
            except Exception as e:
                errors.append(f"User {user_id} exception: {str(e)}")
                await asyncio.sleep(1)  # 에러 시 잠시 대기
    
    async def write_throughput_test(self, duration_seconds: int = 30) -> LoadTestResult:
        """쓰기 처리량 테스트 (목표: > 100 TPS)"""
        logger.info(f"Running write throughput test for {duration_seconds}s")
        
        results = []
        errors = []
        start_time = time.time()
        
        # 동시 쓰기 작업 실행
        tasks = []
        for worker_id in range(10):  # 10개 워커
            task = asyncio.create_task(
                self._write_worker(worker_id, start_time + duration_seconds, results, errors)
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        actual_duration = time.time() - start_time
        
        # 결과 분석
        successful_writes = [r for r in results if r["success"]]
        failed_writes = [r for r in results if not r["success"]]
        
        if successful_writes:
            response_times = [r["response_time_ms"] for r in successful_writes]
            avg_response_time = statistics.mean(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)]
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
            max_response_time = min_response_time = 0
        
        tps = len(successful_writes) / actual_duration
        success_rate = len(successful_writes) / len(results) * 100 if results else 0
        
        return LoadTestResult(
            test_name="Write Throughput Test",
            concurrent_users=10,
            total_requests=len(results),
            duration_seconds=actual_duration,
            requests_per_second=tps,
            successful_requests=len(successful_writes),
            failed_requests=len(failed_writes),
            success_rate=success_rate,
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            max_response_time_ms=max_response_time,
            min_response_time_ms=min_response_time,
            errors=errors[:10],
            goal_achieved=tps >= 100 and success_rate >= 95  # 목표: 100 TPS, 95% 성공률
        )
    
    async def _write_worker(self, worker_id: int, end_time: float, 
                          results: List, errors: List):
        """쓰기 워커"""
        write_count = 0
        
        while time.time() < end_time:
            try:
                # Neo4j에 직접 쓰기 (더 정확한 TPS 측정)
                company_id = f"load-test-write-{worker_id}-{write_count}"
                
                start_time = time.time()
                
                query = """
                CREATE (c:Company {
                    id: $company_id,
                    name: $name,
                    sector: 'LoadTest',
                    risk_score: $risk_score,
                    created_at: timestamp()
                })
                """
                
                driver.execute_write(
                    query,
                    company_id=company_id,
                    name=f"Load Test Company {worker_id}-{write_count}",
                    risk_score=5.0 + (write_count % 5)
                )
                
                response_time = (time.time() - start_time) * 1000
                
                results.append({
                    "success": True,
                    "response_time_ms": response_time,
                    "worker_id": worker_id,
                    "write_count": write_count
                })
                
                write_count += 1
                
                # 쓰기 간격 조정 (TPS 제어)
                await asyncio.sleep(0.01)  # 100 TPS 목표
                
            except Exception as e:
                response_time = (time.time() - start_time) * 1000 if 'start_time' in locals() else 1000
                
                results.append({
                    "success": False,
                    "response_time_ms": response_time,
                    "worker_id": worker_id,
                    "error": str(e)
                })
                
                errors.append(f"Worker {worker_id}: {str(e)}")
                await asyncio.sleep(0.1)  # 에러 시 짧은 대기
    
    async def mixed_workload_test(self, duration_seconds: int = 60) -> LoadTestResult:
        """혼합 워크로드 테스트 (읽기 80%, 쓰기 20%)"""
        logger.info(f"Running mixed workload test for {duration_seconds}s")
        
        results = []
        errors = []
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        # 읽기/쓰기 워커 동시 실행
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # 읽기 워커 (80%)
            for i in range(8):
                task = asyncio.create_task(
                    self._simulate_user_read_activity(session, i, end_time, results, errors)
                )
                tasks.append(task)
            
            # 쓰기 워커 (20%)
            for i in range(2):
                task = asyncio.create_task(
                    self._write_worker(f"mixed-{i}", end_time, results, errors)
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks)
        
        actual_duration = time.time() - start_time
        
        # 결과 분석
        successful_requests = [r for r in results if r.get("success", False)]
        failed_requests = [r for r in results if not r.get("success", True)]
        
        if successful_requests:
            response_times = [r["response_time_ms"] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
            p99_response_time = sorted(response_times)[int(len(response_times) * 0.99)]
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
            max_response_time = min_response_time = 0
        
        rps = len(results) / actual_duration
        success_rate = len(successful_requests) / len(results) * 100 if results else 0
        
        return LoadTestResult(
            test_name="Mixed Workload Test",
            concurrent_users=10,
            total_requests=len(results),
            duration_seconds=actual_duration,
            requests_per_second=rps,
            successful_requests=len(successful_requests),
            failed_requests=len(failed_requests),
            success_rate=success_rate,
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            max_response_time_ms=max_response_time,
            min_response_time_ms=min_response_time,
            errors=errors[:10],
            goal_achieved=rps >= 75 and success_rate >= 90  # 혼합 워크로드 목표
        )
    
    async def run_all_load_tests(self) -> Dict[str, Any]:
        """모든 부하 테스트 실행"""
        logger.info("Starting comprehensive load testing")
        
        # 테스트 데이터 설정
        await self.setup_test_data()
        
        # 부하 테스트 실행
        tests = [
            await self.concurrent_read_test(concurrent_users=100, duration_seconds=30),
            await self.write_throughput_test(duration_seconds=30),
            await self.mixed_workload_test(duration_seconds=60)
        ]
        
        self.results = tests
        
        # 결과 요약
        total_tests = len(tests)
        passed_tests = sum(1 for t in tests if t.goal_achieved)
        
        summary = {
            "load_test_timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "overall_success_rate": passed_tests / total_tests * 100,
            "sprint1_load_goals_met": passed_tests >= 2,
            "performance_summary": {
                "concurrent_reads": f"{tests[0].requests_per_second:.1f} RPS",
                "write_throughput": f"{tests[1].requests_per_second:.1f} TPS",
                "mixed_workload": f"{tests[2].requests_per_second:.1f} RPS"
            },
            "detailed_results": [asdict(t) for t in tests]
        }
        
        return summary
    
    def print_results(self):
        """결과 출력"""
        if not self.results:
            print("No load test results available")
            return
        
        print("\n" + "="*80)
        print("GRAPH SERVICE LOAD TEST RESULTS")
        print("="*80)
        
        for result in self.results:
            status = "✅ PASS" if result.goal_achieved else "❌ FAIL"
            
            print(f"\n{result.test_name}")
            print(f"Status: {status}")
            print(f"Concurrent Users: {result.concurrent_users}")
            print(f"Duration: {result.duration_seconds:.1f}s")
            print(f"Total Requests: {result.total_requests}")
            print(f"RPS/TPS: {result.requests_per_second:.2f}")
            print(f"Success Rate: {result.success_rate:.1f}%")
            print(f"Avg Response Time: {result.avg_response_time_ms:.2f}ms")
            print(f"P95 Response Time: {result.p95_response_time_ms:.2f}ms")
            print(f"P99 Response Time: {result.p99_response_time_ms:.2f}ms")
            if result.errors:
                print(f"Sample Errors: {result.errors[:3]}")
        
        # 전체 요약
        passed = sum(1 for r in self.results if r.goal_achieved)
        total = len(self.results)
        
        print(f"\n" + "-"*80)
        print(f"LOAD TEST SUMMARY")
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        if passed >= total * 0.67:  # 최소 2/3 통과
            print("🚀 Sprint 1 Load Goals: ACHIEVED")
        else:
            print("⚠️  Sprint 1 Load Goals: NEEDS IMPROVEMENT")
        
        print("="*80)


async def main():
    """메인 실행 함수"""
    # 서비스가 실행 중인지 확인
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8003/health") as response:
                if response.status != 200:
                    logger.error("Graph service is not healthy")
                    sys.exit(1)
    except Exception as e:
        logger.error(f"Cannot connect to graph service: {e}")
        logger.error("Please make sure the service is running on port 8003")
        sys.exit(1)
    
    load_test = GraphServiceLoadTest()
    
    try:
        # 부하 테스트 실행
        results = await load_test.run_all_load_tests()
        
        # 결과 출력
        load_test.print_results()
        
        # JSON 파일로 저장
        output_file = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\nDetailed results saved to: {output_file}")
        
        # 목표 달성 여부에 따른 종료 코드
        if results["sprint1_load_goals_met"]:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Load test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
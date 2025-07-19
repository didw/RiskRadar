#!/usr/bin/env python3
"""
메트릭 수집 테스트 스크립트
"""
import asyncio
import requests
import time
from datetime import datetime

async def test_metrics():
    """메트릭 테스트"""
    base_url = "http://localhost:8001"
    
    print("=== Data Service 메트릭 테스트 ===\n")
    
    # 1. 서비스 상태 확인
    try:
        health = requests.get(f"{base_url}/health")
        print(f"1. Health Check: {health.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # 2. 스케줄러 시작
    print("\n2. 스케줄러 시작...")
    try:
        response = requests.post(f"{base_url}/api/v1/scheduler/start")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Scheduler start failed: {e}")
    
    # 3. 잠시 대기 (크롤링이 진행되도록)
    print("\n3. 크롤링 진행 중... (30초 대기)")
    await asyncio.sleep(30)
    
    # 4. 메트릭 확인
    print("\n4. Prometheus 메트릭 확인:")
    try:
        metrics = requests.get(f"{base_url}/metrics")
        if metrics.status_code == 200:
            # 메트릭 내용 일부만 출력
            lines = metrics.text.split('\n')
            for line in lines:
                if line and not line.startswith('#'):
                    if any(keyword in line for keyword in [
                        'data_service_crawl_requests_total',
                        'data_service_articles_processed_total',
                        'data_service_kafka_messages_sent_total',
                        'data_service_current_throughput_articles_per_hour',
                        'data_service_deduplication_rate'
                    ]):
                        print(f"   {line}")
        else:
            print(f"❌ Metrics endpoint returned {metrics.status_code}")
    except Exception as e:
        print(f"❌ Metrics fetch failed: {e}")
    
    # 5. 메트릭 통계 확인
    print("\n5. 메트릭 통계:")
    try:
        stats = requests.get(f"{base_url}/api/v1/metrics/stats")
        if stats.status_code == 200:
            data = stats.json()
            print(f"   Uptime: {data.get('uptime_seconds', 0):.1f} seconds")
            print(f"   Article counts: {data.get('article_counts', {})}")
            print(f"   Duplicate counts: {data.get('duplicate_counts', {})}")
            print(f"   Deduplication rates: {data.get('deduplication_rates', {})}")
    except Exception as e:
        print(f"❌ Metrics stats failed: {e}")
    
    # 6. 스케줄러 통계 확인
    print("\n6. 스케줄러 통계:")
    try:
        scheduler_stats = requests.get(f"{base_url}/api/v1/scheduler/stats")
        if scheduler_stats.status_code == 200:
            data = scheduler_stats.json()
            print(f"   Total crawls: {data.get('total_crawls', 0)}")
            print(f"   Successful crawls: {data.get('successful_crawls', 0)}")
            print(f"   Failed crawls: {data.get('failed_crawls', 0)}")
            print(f"   Total articles: {data.get('total_articles', 0)}")
            print(f"   Throughput: {data.get('throughput_per_hour', 0):.1f} articles/hour")
            print(f"   Average latency: {data.get('average_latency', 0):.1f} seconds")
            print(f"   Running tasks: {data.get('running_tasks', [])}")
    except Exception as e:
        print(f"❌ Scheduler stats failed: {e}")
    
    # 7. 태스크 상태 확인
    print("\n7. 스케줄러 태스크 상태:")
    try:
        tasks = requests.get(f"{base_url}/api/v1/scheduler/tasks")
        if tasks.status_code == 200:
            data = tasks.json()
            for task in data.get('tasks', []):
                print(f"   - {task['source_id']}: "
                      f"running={task.get('is_running', False)}, "
                      f"failures={task.get('consecutive_failures', 0)}")
    except Exception as e:
        print(f"❌ Scheduler tasks failed: {e}")
    
    # 8. 다시 메트릭 확인 (변화 관찰)
    print("\n8. 추가 크롤링 후 메트릭 재확인 (30초 대기)...")
    await asyncio.sleep(30)
    
    try:
        metrics = requests.get(f"{base_url}/metrics")
        if metrics.status_code == 200:
            lines = metrics.text.split('\n')
            print("\n   주요 메트릭 현황:")
            for line in lines:
                if line and not line.startswith('#'):
                    if 'data_service_crawl_requests_total' in line and 'success' in line:
                        print(f"   ✅ {line}")
                    elif 'data_service_articles_processed_total' in line and 'processed' in line:
                        print(f"   📄 {line}")
                    elif 'data_service_current_throughput_articles_per_hour' in line:
                        print(f"   📊 {line}")
    except Exception as e:
        print(f"❌ Final metrics check failed: {e}")
    
    # 9. 스케줄러 중지
    print("\n9. 스케줄러 중지...")
    try:
        response = requests.post(f"{base_url}/api/v1/scheduler/stop")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Scheduler stop failed: {e}")
    
    print("\n=== 테스트 완료 ===")


if __name__ == "__main__":
    print(f"시작 시간: {datetime.now()}")
    asyncio.run(test_metrics())
    print(f"\n종료 시간: {datetime.now()}")
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from main import app
from src.api.models import CrawlerStatus


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


class TestCrawlerAPI:
    """크롤러 API 테스트"""
    
    def test_get_crawler_status(self, client):
        """크롤러 상태 조회 테스트"""
        response = client.get("/api/v1/crawler/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "crawlers" in data
        assert len(data["crawlers"]) == 5  # 5개 크롤러
        
        # 각 크롤러에 필요한 필드가 있는지 확인
        for crawler in data["crawlers"]:
            assert "id" in crawler
            assert "source" in crawler
            assert "status" in crawler
            assert "items_collected" in crawler
            assert "error_count" in crawler
    
    def test_get_specific_crawler_status(self, client):
        """특정 크롤러 상태 조회 테스트"""
        response = client.get("/api/v1/crawler/chosun/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "chosun"
        assert data["source"] == "조선일보"
        assert data["status"] in ["running", "stopped", "error"]
    
    def test_get_nonexistent_crawler_status(self, client):
        """존재하지 않는 크롤러 상태 조회 테스트"""
        response = client.get("/api/v1/crawler/nonexistent/status")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_trigger_crawl_all_sources(self, client):
        """전체 소스 크롤링 트리거 테스트"""
        with patch('src.api.routes.execute_crawling') as mock_crawl:
            response = client.post("/api/v1/crawl", json={})
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "started"
            assert "5 sources" in data["message"]
            assert data["crawled_count"] == 0
    
    def test_trigger_crawl_specific_source(self, client):
        """특정 소스 크롤링 트리거 테스트"""
        with patch('src.api.routes.execute_crawling') as mock_crawl:
            response = client.post("/api/v1/crawl", json={"source": "chosun", "limit": 5})
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "started"
            assert "1 sources" in data["message"]
    
    def test_trigger_crawl_invalid_source(self, client):
        """유효하지 않은 소스 크롤링 트리거 테스트"""
        response = client.post("/api/v1/crawl", json={"source": "invalid_source"})
        
        assert response.status_code == 400
        assert "Unknown source" in response.json()["detail"]
    
    def test_start_specific_crawler(self, client):
        """특정 크롤러 시작 테스트"""
        with patch('src.api.routes.execute_crawling') as mock_crawl:
            response = client.post("/api/v1/crawler/chosun/start")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "started"
            assert data["source"] == "chosun"
    
    def test_stop_specific_crawler(self, client):
        """특정 크롤러 중지 테스트"""
        response = client.post("/api/v1/crawler/chosun/stop")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "stopped"
        assert data["source"] == "chosun"


class TestStatsAPI:
    """통계 API 테스트"""
    
    def test_get_collection_stats(self, client):
        """수집 통계 조회 테스트"""
        response = client.get("/api/v1/stats/collection")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_items" in data
        assert "by_source" in data
        assert "by_hour" in data
        assert "duplicate_rate" in data
        assert "time_range" in data
        
        assert isinstance(data["total_items"], int)
        assert isinstance(data["duplicate_rate"], float)
    
    def test_get_collection_stats_with_time_range(self, client):
        """시간 범위가 있는 수집 통계 조회 테스트"""
        from_time = "2024-07-19T00:00:00"
        to_time = "2024-07-19T23:59:59"
        
        response = client.get(
            f"/api/v1/stats/collection?from_time={from_time}&to_time={to_time}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "time_range" in data
        assert data["time_range"]["from"] is not None
        assert data["time_range"]["to"] is not None


class TestHealthCheck:
    """헬스 체크 테스트"""
    
    def test_health_check(self, client):
        """헬스 체크 테스트"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "data-service"
        assert "timestamp" in data
        assert "kafka" in data
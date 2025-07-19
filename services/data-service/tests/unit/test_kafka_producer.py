import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

# Mock kafka import
with patch.dict('sys.modules', {'kafka': Mock(), 'kafka.errors': Mock()}):
    from src.kafka.producer import (
        OptimizedKafkaProducer, ProducerConfig, NewsMessage,
        get_producer, close_producer
    )


class TestProducerConfig:
    """ProducerConfig 테스트"""
    
    def test_default_config(self):
        """기본 설정 테스트"""
        config = ProducerConfig()
        
        assert config.bootstrap_servers == "localhost:9092"
        assert config.topic == "raw-news"
        assert config.batch_size == 16384
        assert config.compression_type == "gzip"
        assert config.acks == "1"
    
    @patch.dict('os.environ', {
        'KAFKA_BOOTSTRAP_SERVERS': 'test:9092',
        'KAFKA_TOPIC_RAW_NEWS': 'test-topic',
        'KAFKA_BATCH_SIZE': '32768'
    })
    def test_from_env(self):
        """환경변수에서 설정 로드 테스트"""
        config = ProducerConfig.from_env()
        
        assert config.bootstrap_servers == "test:9092"
        assert config.topic == "test-topic"
        assert config.batch_size == 32768


class TestNewsMessage:
    """NewsMessage 테스트"""
    
    @pytest.fixture
    def sample_message(self):
        """샘플 뉴스 메시지"""
        return NewsMessage(
            id="test-001",
            title="테스트 뉴스",
            content="테스트 뉴스 내용입니다.",
            source="test",
            url="https://test.com/news/1",
            published_at="2024-07-19T10:00:00Z",
            crawled_at="2024-07-19T10:05:00Z",
            summary="테스트 요약",
            author="테스트 기자",
            category="테스트",
            tags=["태그1", "태그2"],
            images=["https://test.com/image.jpg"],
            metadata={"test": "data"}
        )
    
    def test_to_dict(self, sample_message):
        """딕셔너리 변환 테스트"""
        data = sample_message.to_dict()
        
        assert data["id"] == "test-001"
        assert data["title"] == "테스트 뉴스"
        assert data["source"] == "test"
        assert data["tags"] == ["태그1", "태그2"]
        assert data["metadata"]["test"] == "data"
    
    def test_to_json(self, sample_message):
        """JSON 변환 테스트"""
        json_str = sample_message.to_json()
        
        # JSON 파싱 가능한지 확인
        data = json.loads(json_str)
        assert data["id"] == "test-001"
        assert data["title"] == "테스트 뉴스"
    
    def test_none_values_excluded(self):
        """None 값 제외 테스트"""
        message = NewsMessage(
            id="test-001",
            title="테스트",
            content="내용",
            source="test",
            url="https://test.com",
            published_at="2024-07-19T10:00:00Z",
            crawled_at="2024-07-19T10:05:00Z",
            summary=None,  # None 값
            author=None    # None 값
        )
        
        data = message.to_dict()
        assert "summary" not in data
        assert "author" not in data
        assert "id" in data


class TestOptimizedKafkaProducer:
    """OptimizedKafkaProducer 테스트"""
    
    @pytest.fixture
    def config(self):
        """테스트용 설정"""
        return ProducerConfig(
            bootstrap_servers="test:9092",
            topic="test-topic"
        )
    
    @pytest.fixture
    def mock_kafka_producer(self):
        """Mock Kafka Producer"""
        with patch('src.kafka.producer.KafkaProducer') as mock:
            mock_instance = Mock()
            mock.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def producer(self, config, mock_kafka_producer):
        """테스트용 Producer"""
        return OptimizedKafkaProducer(config)
    
    def test_initialization(self, producer, mock_kafka_producer):
        """Producer 초기화 테스트"""
        assert producer.config.topic == "test-topic"
        assert producer.producer == mock_kafka_producer
        assert producer._stats["total_sent"] == 0
    
    def test_send_message(self, producer):
        """단일 메시지 전송 테스트"""
        message = NewsMessage(
            id="test-001",
            title="테스트",
            content="내용",
            source="test",
            url="https://test.com",
            published_at="2024-07-19T10:00:00Z",
            crawled_at="2024-07-19T10:05:00Z"
        )
        
        result = producer.send_message(message)
        assert result is True
        
        # 큐에 메시지가 들어갔는지 확인
        assert producer._message_queue.qsize() == 1
    
    def test_send_messages_batch(self, producer):
        """배치 메시지 전송 테스트"""
        messages = []
        for i in range(5):
            message = NewsMessage(
                id=f"test-{i:03d}",
                title=f"테스트 {i}",
                content="내용",
                source="test",
                url=f"https://test.com/{i}",
                published_at="2024-07-19T10:00:00Z",
                crawled_at="2024-07-19T10:05:00Z"
            )
            messages.append(message)
        
        sent_count = producer.send_messages(messages)
        assert sent_count == 5
        assert producer._message_queue.qsize() == 5
    
    def test_stats(self, producer):
        """통계 조회 테스트"""
        stats = producer.get_stats()
        
        assert "total_sent" in stats
        assert "total_failed" in stats
        assert "total_bytes" in stats
        assert "uptime_seconds" in stats
        assert "messages_per_second" in stats
        assert "queue_size" in stats
        assert "is_connected" in stats
    
    def test_health_check_healthy(self, producer, mock_kafka_producer):
        """헬스체크 정상 상태 테스트"""
        mock_kafka_producer.bootstrap_connected.return_value = True
        
        health = producer.health_check()
        
        assert health["status"] == "healthy"
        assert health["connected"] is True
        assert health["topic"] == "test-topic"
    
    def test_health_check_unhealthy(self, producer, mock_kafka_producer):
        """헬스체크 비정상 상태 테스트"""
        mock_kafka_producer.bootstrap_connected.side_effect = Exception("Connection failed")
        
        health = producer.health_check()
        
        assert health["status"] == "unhealthy"
        assert "Connection failed" in health["reason"]
    
    @patch('src.kafka.producer.threading.Thread')
    def test_start_batch_processing(self, mock_thread, producer):
        """배치 처리 시작 테스트"""
        producer.start_batch_processing()
        
        assert producer._running is True
        mock_thread.assert_called_once()
    
    def test_stop_batch_processing(self, producer):
        """배치 처리 중지 테스트"""
        # 배치 처리 시작
        producer._running = True
        
        # 중지
        producer.stop_batch_processing()
        
        assert producer._running is False
    
    def test_close(self, producer, mock_kafka_producer):
        """Producer 종료 테스트"""
        producer.close()
        
        mock_kafka_producer.flush.assert_called_once()
        mock_kafka_producer.close.assert_called_once()


class TestGlobalProducerInstance:
    """글로벌 Producer 인스턴스 테스트"""
    
    def teardown_method(self):
        """테스트 후 정리"""
        close_producer()
    
    @patch('src.kafka.producer.OptimizedKafkaProducer')
    def test_get_producer_singleton(self, mock_producer_class):
        """싱글톤 패턴 테스트"""
        mock_instance = Mock()
        mock_producer_class.return_value = mock_instance
        
        # 첫 번째 호출
        producer1 = get_producer()
        
        # 두 번째 호출
        producer2 = get_producer()
        
        # 같은 인스턴스여야 함
        assert producer1 == producer2
        
        # Producer는 한 번만 생성되어야 함
        mock_producer_class.assert_called_once()
    
    @patch('src.kafka.producer.OptimizedKafkaProducer')
    def test_close_producer(self, mock_producer_class):
        """Producer 종료 테스트"""
        mock_instance = Mock()
        mock_producer_class.return_value = mock_instance
        
        # Producer 생성
        producer = get_producer()
        
        # 종료
        close_producer()
        
        # close 메서드가 호출되었는지 확인
        mock_instance.close.assert_called_once()


class TestKafkaProducerIntegration:
    """통합 테스트 (실제 Kafka 없이)"""
    
    @pytest.fixture
    def producer_with_mock_batch(self):
        """배치 처리 Mock이 있는 Producer"""
        config = ProducerConfig()
        
        with patch('src.kafka.producer.KafkaProducer') as mock_kafka:
            mock_instance = Mock()
            mock_kafka.return_value = mock_instance
            
            producer = OptimizedKafkaProducer(config)
            
            # 배치 처리 Mock
            with patch.object(producer, '_send_batch') as mock_send_batch:
                yield producer, mock_send_batch
    
    def test_batch_processing_flow(self, producer_with_mock_batch):
        """배치 처리 플로우 테스트"""
        producer, mock_send_batch = producer_with_mock_batch
        
        # 메시지 생성
        messages = []
        for i in range(3):
            message = NewsMessage(
                id=f"test-{i}",
                title=f"제목 {i}",
                content="내용",
                source="test",
                url=f"https://test.com/{i}",
                published_at="2024-07-19T10:00:00Z",
                crawled_at="2024-07-19T10:05:00Z"
            )
            messages.append(message)
        
        # 메시지 전송
        for message in messages:
            producer.send_message(message)
        
        # 배치 처리 실행 (수동)
        batch = []
        while not producer._message_queue.empty():
            batch.append(producer._message_queue.get())
        
        if batch:
            producer._send_batch(batch)
        
        # 배치 전송이 호출되었는지 확인
        mock_send_batch.assert_called()
        
        # 전송된 배치 크기 확인
        call_args = mock_send_batch.call_args[0]
        sent_batch = call_args[0]
        assert len(sent_batch) == 3
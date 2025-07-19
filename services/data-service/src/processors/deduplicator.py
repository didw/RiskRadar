"""
Bloom Filter 기반 중복 제거 시스템
- URL 기반 중복 탐지
- 제목 유사도 기반 중복 탐지
- Redis를 이용한 영구 저장
- 통계 및 모니터링
"""
import hashlib
import logging
import json
import re
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import os

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationConfig:
    """중복 제거 설정"""
    # Bloom Filter 설정
    expected_elements: int = 1000000  # 예상 원소 수
    false_positive_rate: float = 0.001  # 0.1% 오탐율
    
    # 제목 유사도 설정
    title_similarity_threshold: float = 0.8  # 80% 이상 유사하면 중복
    shingle_size: int = 3  # 3-gram 사용
    
    # Redis 설정
    redis_url: str = "redis://localhost:6379"
    redis_prefix: str = "dedup:"
    redis_ttl: int = 86400 * 7  # 7일
    
    # 성능 설정
    batch_size: int = 100
    
    @classmethod
    def from_env(cls) -> 'DeduplicationConfig':
        """환경변수에서 설정 로드"""
        return cls(
            expected_elements=int(os.getenv("DEDUP_EXPECTED_ELEMENTS", "1000000")),
            false_positive_rate=float(os.getenv("DEDUP_FALSE_POSITIVE_RATE", "0.001")),
            title_similarity_threshold=float(os.getenv("DEDUP_TITLE_THRESHOLD", "0.8")),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            redis_prefix=os.getenv("DEDUP_REDIS_PREFIX", "dedup:"),
            redis_ttl=int(os.getenv("DEDUP_TTL_DAYS", "7")) * 86400
        )


class SimpleBloomFilter:
    """메모리 기반 Simple Bloom Filter 구현"""
    
    def __init__(self, expected_elements: int, false_positive_rate: float):
        self.expected_elements = expected_elements
        self.false_positive_rate = false_positive_rate
        
        # 최적 크기 계산
        self.bit_array_size = self._calculate_bit_array_size()
        self.hash_functions_count = self._calculate_hash_functions_count()
        
        # 비트 배열 (set으로 구현)
        self.bit_array = set()
        
        self._elements_added = 0
        
        logger.info(
            f"Bloom Filter initialized: size={self.bit_array_size}, "
            f"hash_functions={self.hash_functions_count}, "
            f"expected_elements={expected_elements}, "
            f"false_positive_rate={false_positive_rate}"
        )
    
    def _calculate_bit_array_size(self) -> int:
        """최적 비트 배열 크기 계산"""
        import math
        n = self.expected_elements
        p = self.false_positive_rate
        
        # m = -(n * ln(p)) / (ln(2)^2)
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return int(m)
    
    def _calculate_hash_functions_count(self) -> int:
        """최적 해시 함수 개수 계산"""
        import math
        m = self.bit_array_size
        n = self.expected_elements
        
        # k = (m / n) * ln(2)
        k = (m / n) * math.log(2)
        return max(1, int(k))
    
    def _hash(self, item: str, seed: int) -> int:
        """해시 함수"""
        # FNV-1a 해시의 변형
        hash_value = 2166136261
        for char in item.encode('utf-8'):
            hash_value ^= char
            hash_value = (hash_value * 16777619) % (2**32)
        
        # 시드 적용
        hash_value ^= seed
        hash_value = (hash_value * 16777619) % (2**32)
        
        return hash_value % self.bit_array_size
    
    def add(self, item: str):
        """항목 추가"""
        for i in range(self.hash_functions_count):
            hash_value = self._hash(item, i)
            self.bit_array.add(hash_value)
        
        self._elements_added += 1
    
    def contains(self, item: str) -> bool:
        """항목 포함 여부 확인"""
        for i in range(self.hash_functions_count):
            hash_value = self._hash(item, i)
            if hash_value not in self.bit_array:
                return False
        return True
    
    def get_stats(self) -> Dict[str, any]:
        """통계 정보 반환"""
        current_false_positive_rate = self.estimate_false_positive_rate()
        
        return {
            "bit_array_size": self.bit_array_size,
            "hash_functions_count": self.hash_functions_count,
            "elements_added": self._elements_added,
            "bits_set": len(self.bit_array),
            "fill_ratio": len(self.bit_array) / self.bit_array_size,
            "expected_false_positive_rate": self.false_positive_rate,
            "estimated_false_positive_rate": current_false_positive_rate
        }
    
    def estimate_false_positive_rate(self) -> float:
        """현재 오탐율 추정"""
        if self._elements_added == 0:
            return 0.0
        
        # (1 - e^(-k*n/m))^k
        import math
        k = self.hash_functions_count
        n = self._elements_added
        m = self.bit_array_size
        
        try:
            rate = (1 - math.exp(-k * n / m)) ** k
            return min(rate, 1.0)
        except (OverflowError, ZeroDivisionError):
            return 1.0


class RedisBloomFilter:
    """Redis 기반 Bloom Filter (Redis Modules의 RedisBloom 없이)"""
    
    def __init__(self, redis_client, key_prefix: str, config: DeduplicationConfig):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.config = config
        
        # 메모리 기반 Bloom Filter와 동일한 계산
        self.bit_array_size = self._calculate_bit_array_size()
        self.hash_functions_count = self._calculate_hash_functions_count()
        
        self.redis_key = f"{key_prefix}:bloom_filter"
        
    def _calculate_bit_array_size(self) -> int:
        """최적 비트 배열 크기 계산"""
        import math
        n = self.config.expected_elements
        p = self.config.false_positive_rate
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return int(m)
    
    def _calculate_hash_functions_count(self) -> int:
        """최적 해시 함수 개수 계산"""
        import math
        m = self.bit_array_size
        n = self.config.expected_elements
        k = (m / n) * math.log(2)
        return max(1, int(k))
    
    def _hash(self, item: str, seed: int) -> int:
        """해시 함수"""
        hash_value = 2166136261
        for char in item.encode('utf-8'):
            hash_value ^= char
            hash_value = (hash_value * 16777619) % (2**32)
        
        hash_value ^= seed
        hash_value = (hash_value * 16777619) % (2**32)
        
        return hash_value % self.bit_array_size
    
    def add(self, item: str):
        """항목 추가"""
        pipeline = self.redis.pipeline()
        
        for i in range(self.hash_functions_count):
            bit_offset = self._hash(item, i)
            pipeline.setbit(self.redis_key, bit_offset, 1)
        
        pipeline.expire(self.redis_key, self.config.redis_ttl)
        pipeline.execute()
    
    def contains(self, item: str) -> bool:
        """항목 포함 여부 확인"""
        pipeline = self.redis.pipeline()
        
        for i in range(self.hash_functions_count):
            bit_offset = self._hash(item, i)
            pipeline.getbit(self.redis_key, bit_offset)
        
        results = pipeline.execute()
        return all(results)


@dataclass
class DuplicationResult:
    """중복 검사 결과"""
    is_duplicate: bool
    duplicate_type: str  # 'url', 'title', 'none'
    similarity_score: float
    duplicate_id: Optional[str] = None
    reason: str = ""


class NewsDeduplicator:
    """뉴스 중복 제거 시스템"""
    
    def __init__(self, config: Optional[DeduplicationConfig] = None):
        self.config = config or DeduplicationConfig.from_env()
        
        # Redis 연결
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(self.config.redis_url)
                # 연결 테스트
                self.redis_client.ping()
                logger.info(f"Connected to Redis: {self.config.redis_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}, using memory-only mode")
                self.redis_client = None
        
        # Bloom Filter 초기화
        if self.redis_client:
            self.url_bloom_filter = RedisBloomFilter(
                self.redis_client, 
                f"{self.config.redis_prefix}urls",
                self.config
            )
        else:
            self.url_bloom_filter = SimpleBloomFilter(
                self.config.expected_elements,
                self.config.false_positive_rate
            )
        
        # 통계
        self._stats = {
            "total_checked": 0,
            "duplicates_found": 0,
            "url_duplicates": 0,
            "title_duplicates": 0,
            "start_time": datetime.now()
        }
    
    def _normalize_url(self, url: str) -> str:
        """URL 정규화"""
        # 쿼리 파라미터 제거
        url = re.sub(r'\?.*$', '', url)
        # 프래그먼트 제거
        url = re.sub(r'#.*$', '', url)
        # 트래킹 파라미터 제거
        url = re.sub(r'[?&](utm_|ref|fbclid|gclid).*?(&|$)', '', url)
        # 소문자 변환
        return url.lower().strip()
    
    def _generate_title_shingles(self, title: str) -> Set[str]:
        """제목을 shingle로 변환"""
        # 텍스트 정규화
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Shingle 생성
        words = normalized.split()
        shingles = set()
        
        for i in range(len(words) - self.config.shingle_size + 1):
            shingle = ' '.join(words[i:i + self.config.shingle_size])
            shingles.add(shingle)
        
        return shingles
    
    def _calculate_jaccard_similarity(self, shingles1: Set[str], shingles2: Set[str]) -> float:
        """Jaccard 유사도 계산"""
        if not shingles1 or not shingles2:
            return 0.0
        
        intersection = len(shingles1.intersection(shingles2))
        union = len(shingles1.union(shingles2))
        
        return intersection / union if union > 0 else 0.0
    
    def _check_url_duplicate(self, url: str) -> bool:
        """URL 기반 중복 확인"""
        normalized_url = self._normalize_url(url)
        url_hash = hashlib.sha256(normalized_url.encode()).hexdigest()
        
        return self.url_bloom_filter.contains(url_hash)
    
    def _check_title_duplicate(self, title: str) -> Tuple[bool, float, Optional[str]]:
        """제목 기반 중복 확인"""
        if not self.redis_client:
            # Redis가 없으면 제목 중복 검사 스킵
            return False, 0.0, None
        
        current_shingles = self._generate_title_shingles(title)
        if not current_shingles:
            return False, 0.0, None
        
        # 제목 해시 생성
        title_hash = hashlib.sha256(title.encode()).hexdigest()[:16]
        
        # 기존 제목들과 비교
        pattern = f"{self.config.redis_prefix}title:*"
        existing_keys = self.redis_client.keys(pattern)
        
        max_similarity = 0.0
        duplicate_id = None
        
        for key in existing_keys[:100]:  # 최대 100개만 확인 (성능)
            try:
                stored_data = self.redis_client.get(key)
                if stored_data:
                    stored_shingles = set(json.loads(stored_data))
                    similarity = self._calculate_jaccard_similarity(current_shingles, stored_shingles)
                    
                    if similarity > max_similarity:
                        max_similarity = similarity
                        if similarity >= self.config.title_similarity_threshold:
                            duplicate_id = key.decode().split(':')[-1]
            except Exception as e:
                logger.warning(f"Error comparing with stored title: {e}")
        
        is_duplicate = max_similarity >= self.config.title_similarity_threshold
        
        if not is_duplicate:
            # 새 제목 저장
            title_key = f"{self.config.redis_prefix}title:{title_hash}"
            self.redis_client.setex(
                title_key,
                self.config.redis_ttl,
                json.dumps(list(current_shingles))
            )
        
        return is_duplicate, max_similarity, duplicate_id
    
    def is_duplicate(self, article_data: Dict[str, any]) -> DuplicationResult:
        """기사 중복 여부 확인"""
        self._stats["total_checked"] += 1
        
        url = article_data.get('url', '')
        title = article_data.get('title', '')
        article_id = article_data.get('id', '')
        
        try:
            # 1. URL 기반 중복 확인
            if url and self._check_url_duplicate(url):
                self._stats["duplicates_found"] += 1
                self._stats["url_duplicates"] += 1
                
                return DuplicationResult(
                    is_duplicate=True,
                    duplicate_type='url',
                    similarity_score=1.0,
                    reason=f"URL already exists: {url}"
                )
            
            # 2. 제목 기반 중복 확인
            if title:
                is_title_dup, similarity, dup_id = self._check_title_duplicate(title)
                if is_title_dup:
                    self._stats["duplicates_found"] += 1
                    self._stats["title_duplicates"] += 1
                    
                    return DuplicationResult(
                        is_duplicate=True,
                        duplicate_type='title',
                        similarity_score=similarity,
                        duplicate_id=dup_id,
                        reason=f"Similar title found (similarity: {similarity:.3f})"
                    )
            
            # 3. 중복이 아님 - 등록
            if url:
                normalized_url = self._normalize_url(url)
                url_hash = hashlib.sha256(normalized_url.encode()).hexdigest()
                self.url_bloom_filter.add(url_hash)
            
            return DuplicationResult(
                is_duplicate=False,
                duplicate_type='none',
                similarity_score=0.0,
                reason="No duplicates found"
            )
            
        except Exception as e:
            logger.error(f"Error checking duplicate for article {article_id}: {e}")
            # 에러 시 중복이 아닌 것으로 처리 (데이터 손실 방지)
            return DuplicationResult(
                is_duplicate=False,
                duplicate_type='none',
                similarity_score=0.0,
                reason=f"Error during check: {e}"
            )
    
    def get_stats(self) -> Dict[str, any]:
        """통계 정보 반환"""
        stats = self._stats.copy()
        
        # 런타임 계산
        uptime = datetime.now() - stats["start_time"]
        stats["uptime_seconds"] = uptime.total_seconds()
        
        # 비율 계산
        if stats["total_checked"] > 0:
            stats["duplicate_rate"] = stats["duplicates_found"] / stats["total_checked"]
            stats["url_duplicate_rate"] = stats["url_duplicates"] / stats["total_checked"]
            stats["title_duplicate_rate"] = stats["title_duplicates"] / stats["total_checked"]
        else:
            stats["duplicate_rate"] = 0.0
            stats["url_duplicate_rate"] = 0.0
            stats["title_duplicate_rate"] = 0.0
        
        # Bloom Filter 통계
        if hasattr(self.url_bloom_filter, 'get_stats'):
            stats["bloom_filter"] = self.url_bloom_filter.get_stats()
        
        # Redis 연결 상태
        stats["redis_connected"] = self.redis_client is not None
        
        return stats
    
    def health_check(self) -> Dict[str, any]:
        """헬스 체크"""
        try:
            health = {
                "status": "healthy",
                "redis_connected": False,
                "bloom_filter_type": "memory"
            }
            
            if self.redis_client:
                # Redis 연결 테스트
                self.redis_client.ping()
                health["redis_connected"] = True
                health["bloom_filter_type"] = "redis"
            
            return health
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "redis_connected": False
            }


# 글로벌 인스턴스
_deduplicator_instance: Optional[NewsDeduplicator] = None


def get_deduplicator() -> NewsDeduplicator:
    """글로벌 중복 제거기 인스턴스 반환"""
    global _deduplicator_instance
    
    if _deduplicator_instance is None:
        config = DeduplicationConfig.from_env()
        _deduplicator_instance = NewsDeduplicator(config)
    
    return _deduplicator_instance


def close_deduplicator():
    """글로벌 중복 제거기 종료"""
    global _deduplicator_instance
    
    if _deduplicator_instance and _deduplicator_instance.redis_client:
        try:
            _deduplicator_instance.redis_client.close()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
    
    _deduplicator_instance = None
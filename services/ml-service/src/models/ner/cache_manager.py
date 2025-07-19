"""
NER 결과 캐싱 시스템
NER Results Caching System
"""
import time
import hashlib
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import OrderedDict
import json
from ...kafka.schemas import Entity

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """캐시 엔트리"""
    entities: List[Entity]
    timestamp: float
    hit_count: int = 0
    processing_time_ms: float = 0


class LRUCache:
    """LRU (Least Recently Used) 캐시"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0
        }
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """캐시에서 값 조회"""
        self.stats["total_requests"] += 1
        
        if key in self.cache:
            # 최근 사용으로 이동
            entry = self.cache.pop(key)
            self.cache[key] = entry
            entry.hit_count += 1
            
            self.stats["hits"] += 1
            return entry
        else:
            self.stats["misses"] += 1
            return None
    
    def put(self, key: str, entry: CacheEntry):
        """캐시에 값 저장"""
        if key in self.cache:
            # 기존 엔트리 업데이트
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            # 가장 오래된 엔트리 제거
            self.cache.popitem(last=False)
            self.stats["evictions"] += 1
        
        self.cache[key] = entry
    
    def clear(self):
        """캐시 전체 삭제"""
        self.cache.clear()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        hit_rate = (self.stats["hits"] / self.stats["total_requests"] 
                   if self.stats["total_requests"] > 0 else 0)
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "max_size": self.max_size
        }


class NERCacheManager:
    """NER 결과 캐싱 매니저"""
    
    def __init__(self, max_cache_size: int = 1000, ttl_seconds: int = 3600):
        """
        초기화
        
        Args:
            max_cache_size: 최대 캐시 크기
            ttl_seconds: 캐시 TTL (초)
        """
        self.cache = LRUCache(max_cache_size)
        self.ttl_seconds = ttl_seconds
        self.enabled = True
        
        logger.info(f"NER Cache Manager initialized (size: {max_cache_size}, TTL: {ttl_seconds}s)")
    
    def _generate_cache_key(self, text: str, model_config: Dict[str, Any] = None) -> str:
        """캐시 키 생성"""
        # 텍스트와 모델 설정을 조합해서 해시 생성
        content = {
            "text": text.strip(),
            "config": model_config or {}
        }
        
        content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()
    
    def get_cached_result(self, text: str, model_config: Dict[str, Any] = None) -> Optional[List[Entity]]:
        """캐시된 결과 조회"""
        if not self.enabled:
            return None
        
        cache_key = self._generate_cache_key(text, model_config)
        entry = self.cache.get(cache_key)
        
        if entry:
            # TTL 확인
            if time.time() - entry.timestamp <= self.ttl_seconds:
                logger.debug(f"Cache hit for key: {cache_key[:8]}...")
                return entry.entities
            else:
                # 만료된 엔트리 제거
                self._remove_from_cache(cache_key)
                logger.debug(f"Cache expired for key: {cache_key[:8]}...")
        
        return None
    
    def cache_result(self, text: str, entities: List[Entity], 
                    processing_time_ms: float = 0, 
                    model_config: Dict[str, Any] = None):
        """결과 캐싱"""
        if not self.enabled:
            return
        
        cache_key = self._generate_cache_key(text, model_config)
        entry = CacheEntry(
            entities=entities,
            timestamp=time.time(),
            processing_time_ms=processing_time_ms
        )
        
        self.cache.put(cache_key, entry)
        logger.debug(f"Cached result for key: {cache_key[:8]}... ({len(entities)} entities)")
    
    def _remove_from_cache(self, cache_key: str):
        """캐시에서 특정 키 제거"""
        if cache_key in self.cache.cache:
            del self.cache.cache[cache_key]
    
    def invalidate_cache(self, text_pattern: str = None):
        """캐시 무효화"""
        if text_pattern:
            # 특정 패턴과 일치하는 캐시 엔트리 제거
            keys_to_remove = []
            for key in self.cache.cache.keys():
                # 실제로는 더 정교한 패턴 매칭 필요
                if text_pattern in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self._remove_from_cache(key)
                
            logger.info(f"Invalidated {len(keys_to_remove)} cache entries matching pattern")
        else:
            # 전체 캐시 클리어
            self.cache.clear()
            logger.info("Cleared all cache entries")
    
    def cleanup_expired_entries(self):
        """만료된 캐시 엔트리 정리"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.cache.items():
            if current_time - entry.timestamp > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_from_cache(key)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        base_stats = self.cache.get_stats()
        
        # 추가 통계 계산
        total_hit_count = sum(entry.hit_count for entry in self.cache.cache.values())
        avg_processing_time = (
            sum(entry.processing_time_ms for entry in self.cache.cache.values()) / 
            len(self.cache.cache) if self.cache.cache else 0
        )
        
        return {
            **base_stats,
            "enabled": self.enabled,
            "ttl_seconds": self.ttl_seconds,
            "total_hit_count": total_hit_count,
            "avg_cached_processing_time_ms": avg_processing_time
        }
    
    def enable_cache(self):
        """캐시 활성화"""
        self.enabled = True
        logger.info("Cache enabled")
    
    def disable_cache(self):
        """캐시 비활성화"""
        self.enabled = False
        logger.info("Cache disabled")
    
    def resize_cache(self, new_max_size: int):
        """캐시 크기 조정"""
        old_size = self.cache.max_size
        self.cache.max_size = new_max_size
        
        # 크기가 줄어든 경우 오래된 엔트리 제거
        while len(self.cache.cache) > new_max_size:
            self.cache.cache.popitem(last=False)
            self.cache.stats["evictions"] += 1
        
        logger.info(f"Cache resized from {old_size} to {new_max_size}")
    
    def export_cache_data(self) -> Dict[str, Any]:
        """캐시 데이터 내보내기 (디버깅/분석용)"""
        cache_data = {}
        
        for key, entry in self.cache.cache.items():
            cache_data[key] = {
                "entities": [asdict(entity) for entity in entry.entities],
                "timestamp": entry.timestamp,
                "hit_count": entry.hit_count,
                "processing_time_ms": entry.processing_time_ms
            }
        
        return {
            "cache_entries": cache_data,
            "stats": self.get_cache_stats()
        }


# 전역 캐시 매니저 인스턴스
_global_cache_manager: Optional[NERCacheManager] = None


def get_cache_manager() -> NERCacheManager:
    """전역 캐시 매니저 인스턴스 반환"""
    global _global_cache_manager
    
    if _global_cache_manager is None:
        _global_cache_manager = NERCacheManager()
    
    return _global_cache_manager


def configure_cache(max_size: int = 1000, ttl_seconds: int = 3600):
    """캐시 설정"""
    global _global_cache_manager
    _global_cache_manager = NERCacheManager(max_size, ttl_seconds)
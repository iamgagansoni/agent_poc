import time
from typing import Dict, List, Optional, Any
from collections import OrderedDict
from memory.memory_interface import MemoryInterface
from config.settings import SHORT_TERM_MEMORY_EXPIRATION, CACHE_MAX_SIZE

class CacheMemory(MemoryInterface):

    def __init__(self):
        self._cache = OrderedDict()
        self._timestamp = {}
        self._max_size = CACHE_MAX_SIZE
        self._expiration_time = SHORT_TERM_MEMORY_EXPIRATION

    def _evect_if_needed(self):
        current_time = time.time()

        expired_keys = [k for k, ts in self._timestamp.items() 
                        if current_time - ts > self._expiration_time]
        
        for key in expired_keys:
            if key in self._cache:
                self._cache.pop(key)
            self._timestamp.pop(key)
        
        while len(self._cache) > self._max_size:
            oldest_key, _ = self._cache.popitem(last=False)
            if oldest_key in self._timestamp:
                self._timestamp.pop(oldest_key)
    
    def save(self, key : str, data: Dict[str, Any]) -> bool:
        try:
            if key in self._cache:
                self._cache.pop(key)
            self._cache[key] = data
            self._timestamp[key] = time.time()

            self._evect_if_needed()
            return True
        except Exception:
            return False

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        if key not in self._cache:
            return None
        
        current_time = time.time()
        if current_time - self._timestamp.get(key,0) > self._expiration_time:
            self.delete(key)
            return None
        
        data = self._cache.pop(key)
        self._cache[key] = data
        self._timestamp[key] = current_time

        return data
    
    def delete(self, key: str) -> bool:
        try:
            if key in self._cache:
                self._cache.pop(key)
            if key in self._timestamp:
                self._timestamp.pop(key)
            return True
        except Exception:
            return False
        
    def search(self, query : Dict[str,Any]) -> List[Dict[str,Any]]:
        results = []

        for key, data in self._cache.items():

            current_time = time.time()
            if current_time - self._timestamp.get(key,0) > self._expiration_time:
                continue
            
            match = True
            for query_key, query_value in query.items():
                if query_key not in data or data[query_key] != query_value:
                    match = False
                    break
        
            if match:
                results.append(data)
        
        return results

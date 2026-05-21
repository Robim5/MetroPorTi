import time
from dataclasses import dataclass 
from typing import Any, Optional

# cache em memoria com ttl, evita bater na bd a cada pedido

@dataclass
class CacheEntry:
    value: Any
    expires_at: float
    
class TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}
        
    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        # expirou, tira da memoria e finge que nao existia
        if entry.expires_at < time.time():
            self._store.pop(key, None)
            return None
        return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: int = 30) -> None:
        self._store[key] = CacheEntry(value = value, expires_at = time.time() + ttl_seconds)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)
        
    def clear(self) -> None:
        self._store.clear()

cache = TTLCache()

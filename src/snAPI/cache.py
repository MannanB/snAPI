import time, uuid
from random import choice

FIFO = 'FIFO'  # First In, First Out
LRU = 'LRU'  # Least Recently Used
MRU = 'MRU'  # Most Recently Used
LFU = 'LFU'  # Least Frequently Used
RR = 'RR'  # Random Replacement

class MemoryCache:
    def __init__(self, cache=None, cache_policy=LRU, cache_size=10):
        if cache is None:
            self.cache = {}
        self.cache_size = cache_size
        self.cache_policy = cache_policy

    def add_item(self, request, result):
        # hash request in order to not bloat data
        hashed = uuid.uuid3(uuid.NAMESPACE_DNS, request.to_hashable())

        if hashed in self.cache:
            return 

        if len(self.cache) >= self.cache_size:
            if self.cache_policy == MRU:
                # find greates policy value (mru)
                mru = max(list(self.cache.items()), key=lambda e: e[1][1])
                del self.cache[mru[0]]
            elif self.cache_policy == RR:
                # delete random
                del self.cache[choice(list(self.cache.keys()))]
            else:
                # find least policy value (fifo, lru, lfu)
                fifo_lru_lfu = min(list(self.cache.items()), key=lambda e: e[1][1])
                del self.cache[fifo_lru_lfu[0]]

        policy_value = 0
        if self.cache_policy == FIFO:
            policy_value = time.time()
        self.cache[hashed] = [result, policy_value]

    async def add_item_async(self, request, result):
        # hash request in order to not bloat data
        hashed = uuid.uuid3(uuid.NAMESPACE_DNS, request.to_hashable())

        if hashed in self.cache:
            return 

        if len(self.cache) >= self.cache_size:
            if self.cache_policy == MRU:
                # find greates policy value (mru)
                mru = max(list(self.cache.items()), key=lambda e: e[1][1])
                del self.cache[mru[0]]
            elif self.cache_policy == RR:
                # delete random
                del self.cache[choice(list(self.cache.keys()))]
            else:
                # find least policy value (fifo, lru, lfu)
                fifo_lru_lfu = min(list(self.cache.items()), key=lambda e: e[1][1])
                del self.cache[fifo_lru_lfu[0]]

        policy_value = 0
        if self.cache_policy == FIFO:
            policy_value = time.time()
        self.cache[hashed] = [result, policy_value]

    def get_item(self, request):
        hashed = uuid.uuid3(uuid.NAMESPACE_DNS, request.to_hashable())

        if hashed in self.cache:
            if self.cache_policy == LRU or self.cache_policy == MRU:
                self.cache[hashed][1] = time.time()
            elif self.cache_policy == LFU:
                self.cache[hashed][1] += 1
            return self.cache[hashed][0]

    async def get_item_async(self, reqeust):
        hashed = uuid.uuid3(uuid.NAMESPACE_DNS, request.to_hashable())

        if hashed in self.cache:
            if self.cache_policy == LRU or self.cache_policy == MRU:
                self.cache[hashed][1] = time.time()
            elif self.cache_policy == LFU:
                self.cache[hashed][1] += 1
            return self.cache[hashed][0]
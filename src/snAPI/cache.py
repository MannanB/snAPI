import time
import pickle
from random import choice
from threading import Lock

FIFO = 'FIFO'  # First In, First Out
LRU = 'LRU'  # Least Recently Used
MRU = 'MRU'  # Most Recently Used
LFU = 'LFU'  # Least Frequently Used
RR = 'RR'  # Random Replacement


class MemoryCache:
    def __init__(self, cache=None, cache_policy=LRU, cache_size=10):
        if cache is None:
            self.cache = {}
        self.asyncInUse = []
        self.cache_size = cache_size
        self.cache_policy = cache_policy
        self.lock = Lock()

    def add_item(self, url, result, params=None, headers=None):
        if not (params is None):
            params = tuple(params.items())
        if not (headers is None):
            headers = tuple(headers.items())
        with self.lock:  # make sure its thread safe
            if (url, params, headers) in self.cache:
                return  # this should never happend
            if len(self.cache) >= self.cache_size:
                if self.cache_policy == FIFO or self.cache_policy == LRU or self.cache_policy == LFU:
                    # Find the value with the smallest time stamp
                    # The logic for FIFO, MRU, and LFU are all the same. Its just the policy_value that changes
                    # FIFO is the timestamp of creation
                    # LRU is the timestamp of the last time it was retreived
                    # LFU is the frequency
                    # For all of these, we just need to lowest value (Earliest time stamp, least frequency)
                    fifo_lru_lfu = min(list(self.cache.items()), key=lambda e: e[1][1])
                    del self.cache[fifo_lru_lfu[0]]
                elif self.cache_policy == MRU:
                    # Find the value with the largest time stamp
                    mru = max(list(self.cache.items()), key=lambda e: e[1][1])
                    del self.cache[mru[0]]
                if self.cache_policy == RR:
                    # Delete a random value
                    del self.cache[choice(list(self.cache.keys()))]

            policy_value = 0
            if self.cache_policy == FIFO:
                policy_value = time.time()
            self.cache[(url, params, headers)] = [result, policy_value]

    async def add_item_async(self, url, result, params=None, headers=None):
        if not (params is None):
            params = tuple(params.items())
        if not (headers is None):
            headers = tuple(headers.items())
        with self.lock:  # make sure its thread safe
            if len(self.cache) >= self.cache_size:
                if self.cache_policy == FIFO or self.cache_policy == LRU or self.cache_policy == LFU:
                    # Look at add_item for comments
                    fifo_lru = min(list(self.cache.items()), key=lambda e: e[1][1])
                    del self.cache[fifo_lru[0]]
                elif self.cache_policy == MRU:
                    # Find the value with the largest time stamp
                    mru = max(list(self.cache.items()), key=lambda e: e[1][1])
                    del self.cache[mru[0]]
                if self.cache_policy == RR:
                    # Delete a random value
                    del self.cache[choice(list(self.cache.keys()))]

            policy_value = 0
            if self.cache_policy == FIFO:
                policy_value = time.time()
            self.cache[(url, params, headers)] = [result, policy_value]

    def get_item(self, url, params=None, headers=None):
        if not (params is None):
            params = tuple(params.items())
        if not (headers is None):
            headers = tuple(headers.items())
        with self.lock:
            if (url, params, headers) in self.cache:
                if self.cache_policy == LRU or self.cache_policy == MRU:
                    self.cache[(url, params, headers)][1] = time.time()
                elif self.cache_policy == LFU:
                    self.cache[(url, params, headers)][1] += 1
                return self.cache[(url, params, headers)][0]

    async def get_item_async(self, url, params=None, headers=None):
        if not (params is None):
            params = tuple(params.items())
        if not (headers is None):
            headers = tuple(headers.items())
        with self.lock:
            if (url, params, headers) in self.cache:
                if self.cache_policy == LRU or self.cache_policy == MRU:
                    self.cache[(url, params, headers)][1] = time.time()
                elif self.cache_policy == LFU:
                    self.cache[(url, params, headers)][1] += 1
                return self.cache[(url, params, headers)][0]
            return None

    def to_file(self, file_path):
        with open(file_path, 'wb') as outfile:
            pickle.dump(self.cache, outfile)
        return self.cache

    def load_file(self, file_path):
        with open(file_path, 'rb') as infile:
            self.cache = pickle.load(infile)
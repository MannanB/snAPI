import time
import random
import unittest
import sys
sys.path.insert(0, r'C:\Users\manna\OneDrive\Documents\Python\snAPI\snAPI\src')
from snAPI.cache import *
from snAPI.sessions import Request, Response

dummy_reqests = [Request(f'https://test{x}.com', params={'x': 0}, headers={'x': 0}) for x in range(20)]
dummy_responses = [Response(f'test{x}', 200) for x in range(20)]

class TestCaching(unittest.TestCase):
    def test_fifo(self):
        cache = MemoryCache(cache_policy=FIFO, cache_size=10)
        for x in range(10):
            cache.add_item(dummy_reqests[x], dummy_responses[x])
        cache.add_item(dummy_reqests[19], dummy_responses[19])
        self.assertEqual(len(cache.cache), 10) # ensure its still 10
        self.assertEqual(cache.get_item(dummy_reqests[0]), None)

    def test_lru(self):
        cache = MemoryCache(cache_policy=LRU, cache_size=10)
        for x in range(10):
            cache.add_item(dummy_reqests[x], dummy_responses[x])
        for x in range(10):
            cache.get_item(dummy_reqests[x])
        cache.add_item(dummy_reqests[19], dummy_responses[19])
        self.assertEqual(len(cache.cache), 10)  # ensure its still 10
        self.assertEqual(cache.get_item(dummy_reqests[0]), None)
        
    def test_mru(self):
        cache = MemoryCache(cache_policy=MRU, cache_size=10)
        for x in range(10):
            cache.add_item(dummy_reqests[x], dummy_responses[x])
        for x in range(10):
            cache.get_item(dummy_reqests[x])
            time.sleep(.01) # give it some time so that the time stamps aren't the same
        cache.add_item(dummy_reqests[19], dummy_responses[19])
        self.assertEqual(len(cache.cache), 10)  # ensure its still 10
        self.assertEqual(cache.get_item(dummy_reqests[9]), None)

    def test_lfu(self):
        cache = MemoryCache(cache_policy=LFU, cache_size=10)
        for x in range(10):
            cache.add_item(dummy_reqests[x], dummy_responses[x])
        for x in range(10):
            for _ in range(x): # the first one will be used the least
                cache.get_item(dummy_reqests[x])

        cache.add_item(dummy_reqests[19], dummy_responses[19])
        self.assertEqual(len(cache.cache), 10)  # ensure its still 10
        self.assertEqual(cache.get_item(dummy_reqests[0]), None)

    def test_rr(self):
        cache = MemoryCache(cache_policy=RR, cache_size=10)
        for x in range(10):
            cache.add_item(dummy_reqests[x], dummy_responses[x])
        random.seed(5)  # The random replacement will always get rid of index 9
        cache.add_item(dummy_reqests[19], dummy_responses[19])
        self.assertEqual(len(cache.cache), 10)  # ensure its still 10
        self.assertEqual(cache.get_item(dummy_reqests[9]), None)








import time
import random
import unittest
import sys
sys.path.insert(0, r'C:\Users\manna\OneDrive\Documents\snAPI\src')
from snAPI.cache import *


class TestCaching(unittest.TestCase):
    def test_fifo(self):
        cache = MemoryCache(cache_policy=FIFO, cache_size=10)
        for x in range(10):
            cache.add_item(f'https://test{x}.com', {'data': f'test{x}'}, params={'x': x}, headers={'x': x})
        cache.add_item('https://test.com', {'data': f'test'}, params={'x':-1}, headers={'x':-1})
        self.assertEqual(len(cache.cache), 10) # ensure its still 10
        self.assertEqual(cache.cache.get(('https://test0.com', (('x', 0),), (('x', 0),))), None)
        self.assertEqual(cache.get_item('https://test.com', params={'x':-1}, headers={'x':-1}), {'data': f'test'})

    def test_lru(self):
        cache = MemoryCache(cache_policy=LRU, cache_size=10)
        for x in range(10):
            cache.add_item(f'https://test{x}.com', {'data': f'test{x}'}, params={'x': x}, headers={'x': x})
        for x in range(10):
            cache.get_item(f'https://test{x}.com', params={'x': x}, headers={'x': x})
        cache.add_item('https://test.com', {'data': f'test'}, params={'x': -1}, headers={'x': -1})
        self.assertEqual(len(cache.cache), 10)  # ensure its still 10
        self.assertEqual(cache.cache.get(('https://test9.com', (('x', 0),), (('x', 0),))), None)
        self.assertEqual(cache.get_item('https://test.com', params={'x':-1}, headers={'x':-1}), {'data': f'test'})

    def test_mru(self):
        cache = MemoryCache(cache_policy=MRU, cache_size=10)
        for x in range(10):
            cache.add_item(f'https://test{x}.com', {'data': f'test{x}'}, params={'x': x}, headers={'x': x})
        for x in range(10):
            cache.get_item(f'https://test{x}.com', params={'x': x}, headers={'x': x})
            time.sleep(0.2)
        cache.add_item('https://test.com', {'data': f'test'}, params={'x': -1}, headers={'x': -1})
        self.assertEqual(len(cache.cache), 10)  # ensure its still 10
        self.assertEqual(cache.cache.get(('https://test9.com', (('x', 9),), (('x', 9),))), None)
        self.assertEqual(cache.get_item('https://test.com', params={'x':-1}, headers={'x':-1}), {'data': f'test'})

    def test_lfu(self):
        cache = MemoryCache(cache_policy=LFU, cache_size=10)
        for x in range(10):
            cache.add_item(f'https://test{x}.com', {'data': f'test{x}'}, params={'x': x}, headers={'x': x})
        for x in range(10):
            for y in range(x): # the first one will be used the least
                out = cache.get_item(f'https://test{x}.com', params={'x': x}, headers={'x': x})
                self.assertEqual(out, {'data': f'test{x}'})

        cache.add_item('https://test.com', {'data': f'test'}, params={'x':-1}, headers={'x':-1})
        self.assertEqual(len(cache.cache), 10) # ensure its still 10
        self.assertEqual(cache.cache.get(('https://test0.com', (('x', 0),), (('x', 0),))), None) # the first one will be gone
        self.assertEqual(cache.get_item('https://test.com', params={'x':-1}, headers={'x':-1}), {'data': f'test'})

    def test_rr(self):
        cache = MemoryCache(cache_policy=RR, cache_size=10)
        for x in range(10):
            cache.add_item(f'https://test{x}.com', {'data': f'test{x}'}, params={'x': x}, headers={'x': x})
        random.seed(5)  # The random replacement will always get rid of index 9
        cache.add_item('https://test.com', {'data': f'test'}, params={'x': -1}, headers={'x': -1})
        self.assertEqual(len(cache.cache), 10)  # ensure its still 10
        self.assertEqual(cache.cache.get(('https://test9.com', (('x', 0),), (('x', 0),))), None)
        self.assertEqual(cache.get_item('https://test.com', params={'x':-1}, headers={'x':-1}), {'data': f'test'})

    def test_fileio(self):
        cache = MemoryCache(cache_policy=FIFO, cache_size=10)
        for x in range(10):
            cache.add_item(f'https://test{x}.com', {'data': f'test{x}'}, params={'x': x}, headers={'x': x})
        cache.to_file('cache_test')
        load_cache = MemoryCache(cache_policy=FIFO, cache_size=10)
        load_cache.load_file('cache_test')
        self.assertEqual(cache.cache, load_cache.cache)








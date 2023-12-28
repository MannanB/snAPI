import unittest
import sys
sys.path.insert(0, r'C:\Users\manna\OneDrive\Documents\Python\snAPI\snAPI\src')
import snAPI
import time


class TestApiClass(unittest.TestCase):
    def test_simple_request(self):
        api = snAPI.API(key=snAPI.Key(key_type=snAPI.PARAMS, name='key', key='sample_key1'), use_cache=True)
        api.add_endpoint('http://127.0.0.1:5000/Simple', name='simple')

        test1 = api.request_endpoint(name='simple', q='simple_request')
        test4 = api.simple(q='simple_request')

        test2 = api.request_endpoints(names=['simple' for _ in range(3)], q=['simple_request' for _ in range(3)])
        test3 = api.request_endpoints(names=['simple' for _ in range(3)],
                                      params=[{'q': 'simple_request'} for _ in
                                              range(3)])
        test5 = api.simple(amount=3, q=['simple_request' for _ in range(3)])
        test6 = api.request_endpoints(amount=3, names='simple', params={'q': 'simple_request'})
        test7 = api.request_endpoints(amount=3, names='simple', q='simple_request')
        test9 = api.simple(amount=3, q='simple_request')

        api.close()
        self.assertEqual(test1.output, test4.output)
        self.assertEqual(test2[0].output, test3[0].output)
        self.assertEqual(test2[0].output, test5[0].output)
        self.assertEqual(test5[0].output, test3[0].output)
        self.assertEqual(test3[0].output, test6[0].output)
        self.assertEqual(test3[0].output, test7[0].output)
        self.assertEqual(test3[0].output, test9[0].output)

    def test_async_request(self):
        api = snAPI.API(key=snAPI.Key(key_type=snAPI.PARAMS, name='key', key='sample_key1'), use_cache=True)
        api.add_endpoint('http://127.0.0.1:5000/Simple', name='simple')

        api.enable_async()

        test1 = api.request_endpoint(name='simple', q='simple_request')
        test4 = api.simple(q='simple_request')

        test2 = api.request_endpoints(names=['simple' for _ in range(3)], q=['simple_request' for _ in range(3)])
        test3 = api.request_endpoints(names=['simple' for _ in range(3)],
                                      params=[{'q': 'simple_request'} for _ in
                                              range(3)])
        test5 = api.simple(amount=3, q=['simple_request' for _ in range(3)])
        test6 = api.request_endpoints(amount=3, names='simple', params={'q': 'simple_request'})
        test7 = api.request_endpoints(amount=3, names='simple', q='simple_request')
        test9 = api.simple(amount=3, q='simple_request')

        api.close()
        self.assertEqual(test1.output, test4.output)
        self.assertEqual(test2[0].output, test3[0].output)
        self.assertEqual(test2[0].output, test5[0].output)
        self.assertEqual(test5[0].output, test3[0].output)
        self.assertEqual(test3[0].output, test6[0].output)
        self.assertEqual(test3[0].output, test7[0].output)
        self.assertEqual(test3[0].output, test9[0].output)

    def test_retry_request(self):
        api = snAPI.API(key=snAPI.Key(key_type=snAPI.PARAMS, name='key', key='sample_key1'), use_cache=True)
        api.add_endpoint('http://127.0.0.1:5000/Retry', name='retry')
        res = api.retry(q='blahblahblah', retries=4)
        self.assertEqual(res.json(), {'data': 'blahblahblah'})

    def test_api_key_rotation_calls(self):
        api = snAPI.API(key=snAPI.Key(key_type=snAPI.PARAMS, name='key', key=['sample_key1', 'sample_key2', 'sample_key3'], n_uses_before_switch=10), use_cache=False)
        api.add_endpoint('http://127.0.0.1:5000/Simple', name='simple')

        self.assertEqual(api.key.current_key, 0)
        for _ in range(10): api.simple(q='rotation_calls')
        self.assertEqual(api.key.current_key, 1)
        api.simple(amount=5, q='rotation_calls')
        self.assertEqual(api.key.current_key, 1)
        api.simple(amount=5, q='rotation_calls')
        self.assertEqual(api.key.current_key, 2)
        api.enable_async()
        for _ in range(10): api.simple(q='rotation_calls')
        self.assertEqual(api.key.current_key, 0)
        api.close()

    def test_params_headers(self):
        api_headers = snAPI.API(key=snAPI.Key(key_type=snAPI.HEADERS, name='key', key='sample_key1'))
        api_headers.add_endpoint('http://127.0.0.1:5000/HeadersTest', name='HeadersTest')
        res = api_headers.request_endpoint(name='HeadersTest')
        self.assertEqual(res.json(), {'data': 'sample_key1'})

        api_params = snAPI.API(key=snAPI.Key(key_type=snAPI.PARAMS, name='key', key='sample_key1'))
        api_params.add_endpoint('http://127.0.0.1:5000/Simple', name='Simple')
        res = api_params.request_endpoint(name='Simple')
        self.assertEqual(res.json(), {'data': None})

    def test_cache(self):
        api = snAPI.API(key=snAPI.Key(key_type=snAPI.PARAMS, name='key', key='sample_key1'), use_cache=True)
        resp1 = api.request_endpoint('http://127.0.0.1:5000/Simple')
        resp2 = api.request_endpoint('http://127.0.0.1:5000/Simple')

        self.assertEqual(len(api.cache.cache), 1)
        self.assertEqual(resp1, resp2)

    def test_errors(self):
        api = snAPI.API(key=snAPI.Key(key_type=snAPI.PARAMS, name='key', key='sample_key1'), use_cache=True)
        try:
            api.request_endpoints('http://127.0.0.1:5000/Simple', params={'abc': 123},
                                  headers={'def': 456})
            self.assertEqual(0, 1)
        except ValueError:
            pass

        try:
            api.request_endpoints('http://127.0.0.1:5000/Simple',
                                  params=[{'abc': 123}, {'abc': 123}],
                                  headers=[{'def': 456}, {'def': 456}, {'def': 456}])
            self.assertEqual(0, 1)
        except ValueError:
            pass

        try:
            api.request_endpoint(params={'abc': 123})
            self.assertEqual(0, 1)
        except ValueError:
            pass

        try:
            api.request_endpoints(params=[{'abc': 123}])
            self.assertEqual(0, 1)
        except ValueError:
            pass

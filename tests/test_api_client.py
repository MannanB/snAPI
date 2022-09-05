import unittest
import snAPI
import time

class TestApiClass(unittest.TestCase):
    def test_simple_request(self):
        api = snAPI.API(key='sample_key1',
                       key_method=snAPI.PARAMS, use_cache=True)
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
        test8 = api.request_endpoints(names='simple', q=['simple_request' for _ in range(3)])
        test9 = api.simple(amount=3, q='simple_request')

        api.close()
        self.assertEqual(test1.output, test4.output)
        self.assertEqual(test2[0].output, test3[0].output)
        self.assertEqual(test2[0].output, test5[0].output)
        self.assertEqual(test5[0].output, test3[0].output)
        self.assertEqual(test3[0].output, test6[0].output)
        self.assertEqual(test3[0].output, test7[0].output)
        self.assertEqual(test3[0].output, test8[0].output)
        self.assertEqual(test3[0].output, test9[0].output)

    def test_async_request(self):
        api = snAPI.API(key='sample_key1',
                       key_method=snAPI.PARAMS, use_cache=True)
        api.add_endpoint('http://127.0.0.1:5000/Simple', name='simple')

        api.toggle_async()

        test1 = api.request_endpoint(name='simple', q='simple_request')
        test4 = api.simple(q='simple_request')

        test2 = api.request_endpoints(names=['simple' for _ in range(3)], q=['simple_request' for _ in range(3)])
        test3 = api.request_endpoints(names=['simple' for _ in range(3)],
                                      params=[{'q': 'simple_request'} for _ in
                                              range(3)])
        test5 = api.simple(amount=3, q=['simple_request' for _ in range(3)])
        test6 = api.request_endpoints(amount=3, names='simple', params={'q': 'simple_request'})
        test7 = api.request_endpoints(amount=3, names='simple', q='simple_request')
        test8 = api.request_endpoints(names='simple', q=['simple_request' for _ in range(3)])
        test9 = api.simple(amount=3, q='simple_request')

        api.close()
        self.assertEqual(test1.output, test4.output)
        self.assertEqual(test2[0].output, test3[0].output)
        self.assertEqual(test2[0].output, test5[0].output)
        self.assertEqual(test5[0].output, test3[0].output)
        self.assertEqual(test3[0].output, test6[0].output)
        self.assertEqual(test3[0].output, test7[0].output)
        self.assertEqual(test3[0].output, test8[0].output)
        self.assertEqual(test3[0].output, test9[0].output)

    def test_retry_request(self):
        api = snAPI.API(key='sample_key1',
                       key_method=snAPI.PARAMS, use_cache=True)
        api.add_endpoint('http://127.0.0.1:5000/Retry', name='retry')
        res = api.retry(q='blahblahblah', retries=4)
        self.assertEqual(res.json(), {'data': 'blahblahblah'})

    def test_api_key_rotation_calls(self):
        api = snAPI.API(key=['sample_key1', 'sample_key2'],
                       rotate_key=True,
                       rotate_method=snAPI.ROTATE_METHOD_CALLS,
                       rotate_max_calls=5,
                       key_method=snAPI.PARAMS, use_cache=False)
        api.add_endpoint('http://127.0.0.1:5000/Simple', name='simple')

        # this test won't fail, but you can look at the results using the api in test_api.py
        for x in range(10):
            api.simple(q='rotation_calls')
        api.simple(amount=10, q='rotation_calls')
        api.toggle_async()
        for x in range(10):
            api.simple(q='rotation_calls')
        # due to the nature of async, when looking at data printed by test_api, the api key wont switch chronologically
        api.simple(amount=10, q='rotation_calls')
        api.close()

    def test_api_key_rotation_time(self):
        api = snAPI.API(key=['sample_key1', 'sample_key2'],
                       rotate_key=True,
                       rotate_method=snAPI.ROTATE_METHOD_TIME,
                       rotate_max_time=30,
                       key_method=snAPI.PARAMS, use_cache=False)
        api.add_endpoint('http://127.0.0.1:5000/Simple', name='simple')

        # this test won't fail, but you can look at the results using the api in test_api.py
        for x in range(10):
            api.simple(q='rotation_time')

        time.sleep(30)
        api.simple(amount=10, q='rotation_time')

        api.close()

    def test_params_headers(self):
        api_headers = snAPI.API(key='sample_key1',
                               key_method=snAPI.HEADERS)
        api_headers.add_endpoint('http://127.0.0.1:5000/HeadersTest', name='HeadersTest')
        res = api_headers.request_endpoint(name='HeadersTest')
        self.assertEqual(res.json(), {'data': 'sample_key1'})

        api_params = snAPI.API(key='sample_key1',
                              key_method=snAPI.PARAMS)
        api_params.add_endpoint('http://127.0.0.1:5000/Simple', name='Simple')
        res = api_params.request_endpoint(name='Simple')
        self.assertEqual(res.json(), {'data': None})

    def test_cache(self):
        api = snAPI.API(key='sample_key1',
                       key_method=snAPI.PARAMS,
                       use_cache=True)
        resp1 = api.request_endpoint(endpoint=snAPI.Endpoint('http://127.0.0.1:5000/Simple'))
        resp2 = api.request_endpoint(endpoint=snAPI.Endpoint('http://127.0.0.1:5000/Simple'))

        self.assertEqual(len(api.cache.cache), 1)
        self.assertEqual(resp1, resp2)

    def test_errors(self):
        api = snAPI.API(key='sample_key1',
                       key_method=snAPI.PARAMS,
                       use_cache=True)
        try:
            api.request_endpoints(endpoints=snAPI.Endpoint('http://127.0.0.1:5000/Simple'), params={'abc': 123},
                                  headers={'def': 456})
        except ValueError:
            pass

        try:
            api.request_endpoints(endpoints=snAPI.Endpoint('http://127.0.0.1:5000/Simple'),
                                  params=[{'abc': 123}, {'abc': 123}],
                                  headers=[{'def': 456}, {'def': 456}, {'def': 456}])
        except ValueError:
            pass

        try:
            api.request_endpoint(params={'abc': 123})
        except ValueError:
            pass
        try:
            api.request_endpoints(params=[{'abc': 123}])
        except ValueError:
            pass

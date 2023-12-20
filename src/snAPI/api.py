import time
import queue
import threading
from .sessions import *
from .cache import MemoryCache
from typing import Optional, Union

PARAMS = 'PARAMS'
HEADERS = 'HEADERS'
AUTH = 'AUTH'

# api = API(key=Key(key_type=AUTH, username='a', password='b'))'
'''
class RotatingKey(Key):
    def __init__(self):
        super().__init__()

class myApi(snapi.API):
    def __init__(self, my_key):
        super.__init__(key=snapi.Key(key=my_key))
        self.add_endpoint("endpoint", name="test")

api = myApi('abc')
api.toggle_async()
res = api.test(amount=5)

'''

class Key:
    def __init__(self, key_type=PARAMS, name=None, key=None, username=None, password=None):
        self.key_type = PARAMS
        self.name = name
        self.key = key
        self.username = username
        self.password = password

        # remove the need to specify key_type if user and password are given
        if self.username and self.password:
            self.key_type = AUTH

        if self.key_type == PARAMS or self.key_type == HEADERS:
            if self.name is None:
                raise ValueError("You must specify key name")
            elif self.key is None:
                raise ValueError("You must specify key value")
        elif self.key_type == AUTH:
            if self.username is None or self.password is None:
                raise ValueError("You must specify both username and password for http auth")
        else:
            raise ValueError("Invalid key type")

    def apply(self, request):
        if self.key_type == PARAMS:
            request.params[self.name] = self.key
        elif self.key_type == HEADERS:
            request.headers[self.name] = self.key
        elif self.key_type == AUTH:
            request.auth = (self.username, self.password)

class API:
    def __init__(self, key = None, use_async = False, cache = None):
        self.endpoints = {}
        self.session = None
        self.use_async = use_async

        self.key = key

        if cache is None:
            self.cache = MemoryCache()
        else:
            self.cache = cache

        self.session = Session(use_async=self.use_async, cache=self.cache)

    def __getattr__(self, name):
        if name in self.endpoints:
            def request_endpoint_filled(amount=1, params=None, headers=None, data=None, max_conns=10, retries=0, retry_delay=1, timeout=300, **kwargs):
                if amount == 1:
                    return self.request_endpoint(name=name, params=params, headers=headers, 
                                                data=data, retries=retries, retry_delay=retry_delay,
                                                timeout=timeout, **kwargs)
                else:
                    return self.request_endpoints(amount=amount, names=name, params=params, headers=headers, 
                                                data=data, max_conns=max_conns, retries=retries, retry_delay=retry_delay,
                                                timeout=timeout, **kwargs)

            return request_endpoint_filled
        else:
            raise ValueError(f'Endpoint "{name}" does not exist')

    def close(self):
        self.session.close()

    def toggle_async(self):
        self.use_async = not self.use_async
        self.session.toggle_async()

    def add_endpoint(self, endpoint, name = None, method=METHOD_GET):
        if name is None:
            name = endpoint
        self.endpoints[name] = (endpoint, method)
        return endpoint

    def request_endpoint(self, name = None, 
                         endpoint = None,
                         params = None,
                         headers = None,
                         data=None,
                         retries = 0,
                         retry_delay=1,
                         timeout=300,
                         **kwargs):
        """
        Request a URL
        :param name: (optional) A specified name for an endpoint
        :param endpoint: (optional) The endpoint url
        :param params: Parameters for call
        :param headers: Headers for cals
        :param retries: Amount of retries if a call returns a non-200 code
        :param retry_delay: Amount of time between calls (seconds)
        :return: A Response object
        """

        # user may supply name or endpoint url.
        # If url is supplied, but not added, method defaults to get/post depending on data

        method = METHOD_POST
        if data is None:
            method = METHOD_GET
        if name is None and endpoint is None:
            raise ValueError('No url was given.')
        elif endpoint is None:
            endpoint, method = self.endpoints[name]
        if params is None:
            # use kwargs as parameters
            params = kwargs
        request = Request(endpoint, method, params, headers, data)
        if self.key:
            self.key.apply(request)
        result = self.session.request(request, retries=retries, retry_delay=retry_delay, timeout=timeout)
        return result

    def request_endpoints(self, amount,
                          names=None, 
                          endpoints=None, 
                          params=None, 
                          headers=None,
                          data=None,
                          max_conns=10, 
                          retries=0, 
                          retry_delay=1, 
                          timeout=300,
                          **kwargs):
        '''Request many urls at once
        :param amount: The amount of requests
        :param names: A list of names of endpoints
        :param endpoints: A list of Endpoint objects
        :param params: A list of parameters for each call
        :param headers: Additional headers for each call
        :param max_conns: Maximum amount of concurrent connections
        :param retries: Amount of retries if a request returns a non-200 code
        :param retry_delay: Amount of time between retries (seconds)
        :return: A list of Responses
        '''

        if names is None and endpoints is None:
            raise ValueError('No url(s) were given.')

        method = METHOD_POST
        if data is None:
            method = METHOD_GET

        if params is None and len(kwargs) > 0:
            params = [{} for _ in range(amount)]
            for key in kwargs.keys():
                for i in range(amount):
                    if isinstance(kwargs[key], list):
                        params[i][key] = kwargs[key][i]
                    else:
                        params[i][key] = kwargs[key]

        requests = []
        for i in range(amount):
            request_param = params
            request_headers = headers
            request_data = data
            request_endpoint = endpoints
            request_method = method

            if isinstance(params, list):
                request_param = params[i]
            if isinstance(headers, list):
                request_headers = params[i]
            if isinstance(names, list):
                request_endpoint, request_method = self.endpoints[names[i]]
            if isinstance(endpoints, list):
                request_endpoint = endpoints[i]
            if isinstance(data, list):
                request_data = data[i]

            if request_endpoint is None: # one name, endpoint=none
                request_endpoint, request_method = self.endpoints[names]

            req = Request(request_endpoint, request_method, request_param, request_headers, request_data)
            self.key.apply(req)
            requests.append(req)

        return self.session.request_bulk(requests, max_conns=max_conns, retries=retries, retry_delay=retry_delay, timeout=timeout, **kwargs)
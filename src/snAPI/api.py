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
    '''
    key = snapi.Key(name="key", key="value", key_type=snapi.PARAMS/HEADERS)
    key = snapi.Key(key="value") # Defaults to PARAMS
    key = snapi.Key(key="value", key_type=snapi.HEADERS)
    key = snapi.Key(key_type=snapi.AUTH, username="user", password="pass")
    key = snapi.Key(username="user", password="pass") # Defaults to AUTH
    '''
    def __init__(self, name=None, key=None, key_type=PARAMS, username=None, password=None, n_uses_before_switch=None, **kwargs):
        self.key_type = key_type
        self.name = name
        self.key = key
        self.username = username
        self.password = password
        self.current_key = 0
        self.n_uses = 0
        self.n_uses_before_switch = n_uses_before_switch

        # remove the need to specify key_type if user and password are given
        if self.username and self.password:
            self.key_type = AUTH

        if isinstance(key, list):
            if n_uses_before_switch is None:
                raise ValueError("You must specify n_uses_before_switch for rotating keys")
            if self.key_type == AUTH:
                raise ValueError("You cannot use rotating keys with http auth")

        if self.key_type == PARAMS or self.key_type == HEADERS:
            if len(kwargs) == 1:
                self.name = list(kwargs.keys())[0]
                self.key = kwargs[self.name]
            if self.name is None:
                self.name = "key" # default to key
            if self.key is None:
                raise ValueError("You must specify key value")
        elif self.key_type == AUTH:
            if self.username is None or self.password is None:
                raise ValueError("You must specify both username and password for http auth")
        else:
            raise ValueError("Invalid key type")

    def apply(self, request):
        key = self.key
        self.n_uses += 1
        # if the key is rotating, check if it needs to be
        if self.n_uses_before_switch and self.n_uses >= self.n_uses_before_switch:
            self.n_uses = 0
            self.current_key = (self.current_key + 1)
            if self.current_key >= len(key):
                self.current_key = 0
        # if its a rotating key, select the correct key
        if isinstance(key, list):
            key = key[self.current_key]
        if self.key_type == PARAMS:
            request.params[self.name] = key
        elif self.key_type == HEADERS:
            request.headers[self.name] = key
        elif self.key_type == AUTH:
            request.auth = (self.username, self.password)
        

class API:
    def __init__(self, key = None, use_async = False, cache = None, use_cache = False):
        self.endpoints = {}
        self.session = None
        self.use_async = use_async

        self.key = key
        
        self.cache = None
        if use_cache:
            if cache is None:
                self.cache = MemoryCache()
            else:
                self.cache = cache

        self.session = Session(use_async=self.use_async, cache=self.cache)

    def __getattr__(self, name):
        if name in self.endpoints:
            def request_endpoint_filled(amount=1, params=None, headers=None, data=None, max_conns=10, retries=0, retry_delay=1, timeout=300, **kwargs):
                if isinstance(params, list): amount = len(params)
                if isinstance(headers, list): amount = len(headers)
                if isinstance(data, list): amount = len(data)
                if amount == 1:
                    return self.request_endpoint(endpoint_name=name, params=params, headers=headers, 
                                                data=data, retries=retries, retry_delay=retry_delay,
                                                timeout=timeout, **kwargs)
                else:
                    return self.request_endpoints(amount=amount, endpoint_names=name, params=params, headers=headers,
                                                data=data, max_conns=max_conns, retries=retries, retry_delay=retry_delay,
                                                timeout=timeout, **kwargs)

            return request_endpoint_filled
        else:
            raise ValueError(f'Endpoint "{name}" does not exist')

    def close(self):
        self.session.close()

    def enable_async(self):
        self.use_async = True
        self.session.use_async = True
    
    def disable_async(self):
        self.use_async = False
        self.session.use_async = False

    def add_endpoint(self, endpoint, endpoint_name=None, method=METHOD_GET):
        if endpoint_name is None:
            endpoint_name = endpoint
        self.endpoints[endpoint_name] = (endpoint, method)
        return endpoint

    def request_endpoint(self, endpoint=None, 
                         endpoint_name=None,
                         params = None,
                         headers = None,
                         data=None,
                         retries = 0,
                         retry_delay=1,
                         timeout=300,
                         **kwargs):
        """
        Request a URL
        :param endpoint_name: (optional) A specified name for an endpoint
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
        if endpoint_name is None and endpoint is None:
            raise ValueError('No url was given.')
        elif endpoint is None:
            endpoint, method = self.endpoints[endpoint_name]
        if params is None:
            # use kwargs as parameters
            params = kwargs
        request = Request(endpoint, method, params, headers, data)
        if self.key:
            self.key.apply(request)
        result = self.session.request(request, retries=retries, retry_delay=retry_delay, timeout=timeout, use_async=self.use_async)
        return result

    def request_endpoints(self, amount=None,
                          endpoints=None,
                          endpoint_names=None,
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
        :param endpoint_names: A list of names of endpoints
        :param endpoints: A list of Endpoint objects
        :param params: A list of parameters for each call
        :param headers: Additional headers for each call
        :param max_conns: Maximum amount of concurrent connections
        :param retries: Amount of retries if a request returns a non-200 code
        :param retry_delay: Amount of time between retries (seconds)
        :return: A list of Responses
        '''

        if endpoint_names is None and endpoints is None:
            raise ValueError('No url(s) were given.')

        method = METHOD_POST
        if data is None:
            method = METHOD_GET

        if params is None and len(kwargs) > 0:
            if amount is None:
                amount = max([len(kwargs[key]) for key in kwargs.keys() if isinstance(kwargs[key], list)])
            params = [{} for _ in range(amount)]
            for key in kwargs.keys():
                for i in range(amount):
                    if isinstance(kwargs[key], list):
                        params[i][key] = kwargs[key][i]
                    else:
                        params[i][key] = kwargs[key]
        
        if isinstance(endpoint_names, list): amount = len(endpoint_names)
        if isinstance(endpoints, list): amount = len(endpoints)
        if isinstance(params, list): amount = len(params)
        if isinstance(headers, list): amount = len(headers)
        if isinstance(data, list): amount = len(data)

        if amount is None:
            raise ValueError('No amount was given. Use request_endpoint for single requests.')

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
            if isinstance(endpoint_names, list):
                request_endpoint, request_method = self.endpoints[endpoint_names[i]]
            if isinstance(endpoints, list):
                request_endpoint = endpoints[i]
            if isinstance(data, list):
                request_data = data[i]

            if request_endpoint is None: # one name, endpoint=none
                request_endpoint, request_method = self.endpoints[endpoint_names]

            req = Request(request_endpoint, request_method, request_param, request_headers, request_data)
            if self.key:
                self.key.apply(req)
            requests.append(req)

        return self.session.request_bulk(requests, max_conns=max_conns, retries=retries, retry_delay=retry_delay, timeout=timeout, use_async=self.use_async, ** kwargs)
    

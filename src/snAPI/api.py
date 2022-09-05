import time
import queue
import threading
from .httpreq import *
from .cache import MemoryCache
from typing import Optional, Union

PARAMS = 'PARAMS'
HEADERS = 'HEADERS'
ROTATE_METHOD_CALLS = 'ROTATE_METHOD_CALLS'
ROTATE_METHOD_TIME = 'ROTATE_METHOD_TIME'


class Endpoint:
    def __init__(self, url, name=None):
        self.name = name
        self.url = url


class API:
    def __init__(self,
                 key_method: int = PARAMS,
                 use_async: bool = False,
                 use_cache: bool = True,
                 cache: MemoryCache = None,
                 rotate_key: bool = False,
                 rotate_method: int = ROTATE_METHOD_CALLS,
                 rotate_max_calls: int = 0,
                 rotate_max_time: int = 0,
                 **kwargs) -> None:
        self.endpoints = {}
        self.session = None
        self.use_async = use_async

        self.rotate_key = rotate_key
        self.key_idx = 0
        self.rotate_method = rotate_method
        self.rotate_max_calls = rotate_max_calls
        self.rotate_max_time = rotate_max_time

        self.key = tuple(kwargs.values())
        self.key_names = tuple(kwargs.keys())
        self.key_method = key_method

        self.calls = 0
        self.last_rotate_time = time.time()
        if self.rotate_key:
            if len(self.key) == 0:
                raise ValueError('No key was given.')
            for key in self.key:
                if isinstance(key, str):
                    raise TypeError('Key rotation requires a list of keys.')
            self.lock = threading.Lock()
            self.rotate_thread_queue = queue.Queue()
            self.rotate_thread = threading.Thread(target=self.rotate_api_key, args=(self.rotate_thread_queue,),daemon=True)
            self.rotate_thread.start()

        if use_cache:
            if cache is None:
                self.cache = MemoryCache()
            else:
                self.cache = cache
        else:
            self.cache = None

        self.session = Session(use_async=self.use_async, cache=self.cache)

    def __getattr__(self, name):
        if name in self.endpoints:
            def request_endpoint_filled(amount=1, params=None, headers=None, session=None, retries=1, retry_delay=1,
                                        use_async=None, ssl=True, **kwargs):
                if amount <= 1:
                    if isinstance(params, list):
                        amount = len(params)
                    elif isinstance(headers, list):
                        amount = len(headers)
                    elif len(kwargs) > 0 and isinstance(kwargs[list(kwargs.keys())[0]], list):
                        amount = len(kwargs[list(kwargs.keys())[0]])
                if amount == 1:
                    return self.request_endpoint(name, params=params, headers=headers, session=session, retries=retries,
                                                 retry_delay=retry_delay, use_async=use_async, ssl=ssl, **kwargs)
                elif amount > 1:
                    return self.request_endpoints(names=[name for _ in range(amount)], params=params, headers=headers,
                                                  session=session, retries=retries, retry_delay=retry_delay,
                                                  use_async=use_async, ssl=ssl, **kwargs)

            return request_endpoint_filled

    def close(self):
        self.session.close()
        if self.rotate_key:
            self.rotate_thread_queue.put(0)  # adding something to the queue disables the while loop
            self.rotate_thread.join()

    def apply_key(self, dct):
        if self.rotate_key:
            with self.lock:
                self.calls += 1

        for i, name in enumerate(self.key_names):
            if self.rotate_key:
                dct[name] = self.key[i][self.key_idx]
            else:
                dct[name] = self.key[i]
        return dct

    def rotate_api_key(self, done_queue):
        while done_queue.empty():
            try:
                with self.lock:
                    if self.rotate_key:
                        if self.rotate_method == ROTATE_METHOD_CALLS:
                            if self.calls >= self.rotate_max_calls:
                                self.key_idx += 1
                                self.calls = 0
                        elif self.rotate_method == ROTATE_METHOD_TIME:
                            if time.time() - self.last_rotate_time >= self.rotate_max_time:
                                self.key_idx += 1
                                self.last_rotate_time = time.time()
                        if self.key_idx >= len(self.key[0]):
                            self.key_idx = 0
            except (KeyboardInterrupt, SystemExit):
                break


    def toggle_async(self):
        self.use_async = not self.use_async
        self.session.toggle_async()

    def add_endpoint(self, endpoint: str,
                     name: Optional[str] = None) -> Endpoint:
        ep = Endpoint(endpoint, name)
        if name is None:
            name = endpoint
        self.endpoints[name] = ep
        return ep

    def request_endpoint(self, name: Optional[str] = None,
                         endpoint: Optional[Endpoint] = None,
                         params: Optional[dict] = None,
                         headers: Optional[dict] = None,
                         session: Optional[Session] = None,
                         retries: int = 1,
                         retry_delay: Union[int, float] = 1,
                         use_async: Optional[bool] = None,
                         ssl: bool = True,
                         **kwargs) -> Response:
        """
        Request a URL
        :param name: A specified name for an endpoint
        :param endpoint: An Endpoint object
        :param params: Parameters for call
        :param headers: Additional headers for call
        :param session: an httpreq.Session(). Leave none for default session
        :param retries: Amount of retries if a call returns a non-200 code
        :param retry_delay: Amount of time between calls (seconds)
        :param use_async: Whether to use async. Leave none for default
        :param ssl: Whether to certify with ssl or not
        :return: A Response object
        """
        if params is None:
            params = kwargs
        if headers is None:
            headers = {}
        if name is None and endpoint is None:
            raise ValueError('No url was given.')
        elif endpoint is None:
            endpoint = self.endpoints[name]
        if self.key_method == PARAMS:
            params = self.apply_key(params)
        else:
            headers = self.apply_key(headers)

        if session is None:
            session = self.session

        result = session.get(endpoint.url, params=params, headers=headers, retries=retries, retry_delay=retry_delay,
                             use_async=use_async, ssl=ssl)
        return result
    
    #TODO: make names and endpoints singular
    def request_endpoints(self, amount: int = 0,
                          names: Optional[Union[str, list[str]]] = None,
                          endpoints: Optional[Union[Endpoint, list[Endpoint]]] = None,
                          params: Optional[Union[dict, list[dict]]] = None,
                          headers: Optional[Union[dict, list[dict]]] = None,
                          session: Optional[Session] = None,
                          max_connections: int = 10,
                          per: int = 1,
                          retries: int = 1,
                          retry_delay: Union[int, float] = 1,
                          use_async: Optional[bool] = None,
                          ssl: Optional[bool] = None,
                          **kwargs) -> list[Response]:
        """
        Request many urls at once
        :param amount: the amount of requests
        :param names: A list of names of endpoints
        :param endpoints: A list of Endpoint objects
        :param params: A list of parameters for each call
        :param headers: Additional headers for each call
        :param session: a httpreq.Session(). Leave none for default session
        :param max_connections: Maximum amount of asyncronous/concurrent connections
        :param per: Amount of time between adding more connections
        :param retries: Amount of retries if a request returns a non-200 code
        :param retry_delay: Amount of time between retries (seconds)
        :param use_async: Whether to use async. Leave none for default
        :param ssl: Whether to certify with ssl or not
        :return: A list of Responses
        """

        # attempt to get the amount of reqeusts any way possible
        # The function will take in either a list or a string/dict for names,endpoints,headers,params,etc

        if names is None and endpoints is None:
            raise ValueError('No url(s) were given.')

        if not amount:
            if isinstance(names, list):
                amount = len(names)
            elif isinstance(endpoints, list):
                amount = len(endpoints)
            elif isinstance(params, list):
                amount = len(params)
            elif isinstance(headers, list):
                amount = len(headers)
            elif len(kwargs) > 0 and isinstance(kwargs[list(kwargs.keys())[0]], list):
                amount = len(kwargs[list(kwargs.keys())[0]])
            else:
                raise ValueError("Amount was not specified in any of the arguments.")

        if params is None and len(kwargs) > 0:
            params = [{} for _ in range(amount)]
            for key in kwargs.keys():
                for i in range(len(params)):
                    if isinstance(kwargs[key], list):
                        params[i][key] = kwargs[key][i]
                    else:
                        params[i][key] = kwargs[key]

        if isinstance(params, dict):
            params = [params for _ in range(amount)]
        if isinstance(headers, dict):
            params = [headers for _ in range(amount)]
        if isinstance(names, str):
            names = [names for _ in range(amount)]
        if isinstance(endpoints, Endpoint):
            endpoints = [endpoints for _ in range(amount)]

        # from this point onwards everything should be in a list

        urls = []
        if not (names is None):
            for name in names:
                urls.append(self.endpoints[name].url)
        else:
            for endpoint in endpoints:
                urls.append(endpoint.url)
        if self.key_method == PARAMS:
            new = False
            if params is None:
                new = True
                params = []
            for i in range(amount):
                if self.key_name in params:
                    continue
                if new:
                    params.append({})
                params[i] = self.apply_key(params[i])
        else:
            new = False
            if headers is None:
                new = True
                headers = []
            for i in range(amount):
                if self.key_name in headers:
                    continue
                if new:
                    headers.append({})
                headers[i] = self.apply_key(headers[i])

        if session is None:
            session = self.session

        if (urls and amount != len(urls)) or (params and amount != len(params)) or (headers and amount != len(headers)):
            raise ValueError('Inconsistent length of urls, parameters, and/or headers.')

        return session.get_bulk(urls, params=params, headers=headers,
                                max_connections=max_connections, per=per, retries=retries, retry_delay=retry_delay,
                                use_async=use_async, ssl=ssl)

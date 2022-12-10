import aiohttp
import asyncio
import requests
from time import sleep
from json import loads as load_json

METHOD_PUT = 'PUT'
METHOD_GET = 'GET'
METHOD_POST = 'POST'
METHOD_HEAD = 'HEAD'
METHOD_DELETE = 'DELETE'
METHOD_OPTIONS = 'OPTIONS'


class Response:
    def __init__(self, output=None, status=200):
        self.output = output
        self.status = status

    def json(self):
        return load_json(self.output)
    
    def __repr__(self):
        return f'Response({self.status})'

class Request:
    def __init__(self, url, method=METHOD_GET, params=None, headers=None, data=None, auth=None):
        '''Defines a request
        :param method: method for the http request
        :param url: URL to be requests
        :param params: (optional) dict of parameters for request
        :param headers: (optional) dict of headers for request
        :param data: (optional) dict of data for request
        '''
        self.url = url
        self.method = method
        self.params = {} if params is None else params
        self.headers = {} if headers is None else headers
        self.data = {} if data is None else data
        self.auth = auth

    def to_hashable(self):
        # hashable data for efficient caching of data
        return str((self.url, tuple(self.params.items()), tuple(self.headers.items()), tuple(self.data.item())))

class Session:
    def __init__(self, use_async = False, verify=True, cache=None, headers=None):
        self.use_async = use_async
        self.verify = verify
        self.cache = cache
        self.headers = headers
        self.session = None
        self.loop = None

    def run_async(self, coroutine):
        if self.loop is None:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
        return self.loop.run_until_complete(coroutine)

    def get_session_sync(self):
        if self.session is None or isinstance(self.session, aiohttp.ClientSession):
            if self.session:
                self.run_async(self.close_async())
            self.session = requests.Session()
        return self.session

    async def get_session_async(self):
        if self.session is None or isinstance(self.session, requests.Session):
            if self.session:
                self.session.close()
            self.session = aiohttp.ClientSession(headers=self.global_headers)
        return self.session

    async def close_async(self) -> None:
            session = await self.get_session_async()
            await session.close()

    def close(self):
        if self.session is None:
            return
        if self.use_async:
            self.run_async(self.close_async())
        else:
            self.session.close()

    def request(self, request, use_async=None, **kwargs):
        '''Sends a Request. returns a Response object. 
        :param request: Request object to be requested
        :param use_async: (optional) defaults to class value
        :param timeout: timeout before it gives up, default 100
        :param retries: amount of retries in case of non-200 response
        :param retry_delay: delay between each retry
        '''
        use_async = use_async if use_async else self.use_async

        if use_async:
            return self.run_async(self.request_async(request, **kwargs))
        else:
            return self.request_sync(request, **kwargs)

    def request_sync(self, request, **kwargs):
        # check if request is cached before doing anything
        if self.cache:
            if cached := self.cache.get(request):
                return cached

        sess = self.get_session_sync()
        
        trys = 0
        while True:
            result = sess.request(request.method, 
                                  url=request.url, 
                                  params=request.params, 
                                  headers=request.headers, 
                                  data=request.data,
                                  timeout=kwargs.get("timeout"), 
                                  auth=request.auth,
                                  verify=self.verify)
            if result.status_code != 200 and trys < kwargs.get("retries", 0):
                if "retry_delay" in kwargs:
                    sleep(kwargs["retry_delay"])
                trys += 1
                continue
            else:
                response = Response(result, result.status_code)
                if self.cache:
                    self.cache.add_item(request, response)
                return response

    async def request_async(self, request, **kwargs):
        # check if request is cached before doing anything
        if self.cache:
            if cached := await self.cache.get_async(request):
                return cached

        sess = self.get_session_async()
        
        trys = 0
        while True:
            async with sess.request(request.method, 
                                    url=request.url, 
                                    params=request.params, 
                                    headers=request.headers, 
                                    data=request.data, 
                                    timeout=kwargs.get("timeout"), 
                                    auth=request.auth, 
                                    ssl=self.verify) as result:

                if result.status != 200 and trys < kwargs.get("retries", 0):
                    if "retry_delay" in kwargs:
                        sleep(kwargs["retry_delay"])
                    trys += 1
                    continue
                else:
                    response = Response(result, result.status_code)
                    if self.cache:
                        await self.cache.add_item_async(request, response)
                    return response

    def request_bulk(self, requests, use_async=None, max_conns=10, **kwargs):
        '''Sends many requests. returns a list of Response objects.
        :param requests: list of Request objects
        :param use_async: (optional) defaults to class value
        :param max_conns: maximum asynchronous connections, default 10
        :param timeout: timeout before it gives up, default 100
        :param auth: HTTP auth, tuple of username+password
        :param retries: amount of retries in case of non-200 response
        :param retry_delay: delay between each retry
        '''
        if use_async:
            return self.run_async(self.request_bulk_async(requests, max_conns, **kwargs))
        else:
            return self.request_bulk_sync(requests, **kwargs)

    def request_bulk_sync(self, requests, **kwargs):
        responses = []
        for request in requests:
            responses.append(self.request_sync(request, **kwargs))
        return responses

    async def request_bulk_async(self, requests, max_conns, **kwargs):
        responses = [None for _ in range(len(requests))]
        running_tasks = {}

        while True:
            for i, task in running_tasks.items():
                if task.done():
                    del running_tasks[i]
                    responses[i] = await task

            if responses.count(None) == 0:
                break

            for i, request in enumerate(requests):
                task = asyncio.create_task(self.request_async(request, **kwargs))
                running_tasks[i] = task

                if len(running_tasks.values()) == max_conns:
                    break
            
            await asyncio.sleep(0.01)
        return responses
                        

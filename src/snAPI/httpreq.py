import aiohttp
import asyncio
import requests
from time import sleep
from .cache import MemoryCache
from typing import Optional, Union
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


class Session:
    """
    "Wrapper" around aiohttp.ClientSession() and requests.session() depending on use_async

    Attributes:
        use_async: A boolean indicating if the session should asyncronously process urls
    """

    def __init__(self,
                 use_async: bool = False,
                 ssl: bool = True,
                 cache: Optional[MemoryCache] = None,
                 headers: Optional[dict] = None) -> None:
        self.global_headers = headers
        self.use_async = use_async
        self.ssl = ssl
        self.session = None
        self.loop = None
        self.cache = cache

    def run_async(self, coroutine):
        if self.loop is None:
            try:
                self.loop = asyncio.get_running_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
        return self.loop.run_until_complete(coroutine)

    def get_session(self) -> requests.Session:
        """
        Gets and changes the session
        :return: requests.Session()
        """
        if self.session is None or isinstance(self.session, aiohttp.ClientSession):
            if self.session:
                self.run_async(self.close_async())
            self.session = requests.Session()
        return self.session

    async def get_session_async(self) -> aiohttp.ClientSession:
        """
        Gets and changes the session
        :return: aiohttp.Session()
        """
        if self.session is None or isinstance(self.session, requests.Session):
            if self.session:
                self.session.close()
            self.session = aiohttp.ClientSession(headers=self.global_headers)
        return self.session

    async def close_async(self) -> None:
        session = await self.get_session_async()
        await session.close()

    def close(self) -> None:
        """
        Closes the session
        :return: None
        """
        if self.session is None:
            return
        if self.use_async:
            self.run_async(self.close_async())
        else:
            self.session.close()

    def toggle_async(self) -> None:
        self.use_async = not self.use_async

    def update_headers(self, headers: dict):
        self.global_headers.update(headers)
        if self.use_async:
            # there is no good way to update headers with aiohttp, so just restart the session
            self.session = None
            self.run_async(self.get_session_async())
        else:
            self.session.headers.update(self.global_headers)

    def validate_url(self, url: str) -> str:
        if len(url) >= 8 and ('https://' == url[:8] or 'http://' == url[:7]):
            # if https:// or http:// isn't in front of the url, add it
            return url
        return 'http://' + url

    def request(self, method: str,
                url: str,
                params: Optional[dict] = None,
                headers: Optional[dict] = None,
                data: Optional[dict] = None,
                session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
                retries: int = 0,
                retry_delay: int = 1,
                use_async: Optional[bool] = None,
                ssl: Optional[bool] = None) -> Response:
        """
        Request a URL
        :param method: HTTP method
        :param url: A Url
        :param params: Parameters for request
        :param headers: Additional headers for request
        :param data: Payload for post/put
        :param session: an aiohttp.Session or requests.Session. Leave none for default session
        :param retries: Amount of retries if a request returns a non-200 code
        :param retry_delay: Amount of time between retries (seconds)
        :param use_async: Whether to use async. Leave none for default
        :param ssl: Whether to certify with ssl or not
        :return: A Response object
        """
        url = self.validate_url(url)

        if use_async is None:
            use_async = self.use_async
        elif use_async != self.use_async:
            self.toggle_async()
        if ssl is None:
            ssl = self.ssl

        if use_async:
            return self.run_async(
                self.request_async(method, url, params=params, headers=headers, data=data, retries=retries,
                                   session=session, retry_delay=retry_delay,
                                   ssl=ssl))
        else:
            return self.request_sync(method, url, params=params, headers=headers, data=data, retries=retries,
                                     retry_delay=retry_delay,
                                     session=session, ssl=ssl)

    def request_sync(self, method: str,
                     url: str,
                     params: Optional[dict] = None,
                     headers: Optional[dict] = None,
                     data: Optional[dict] = None,
                     session: Optional[requests.Session] = None,
                     retries: int = 0,
                     retry_delay: Union[int, float] = 1,
                     ssl: Optional[bool] = None) -> Response:
        if params is None:
            params = {}

        # first check if the result is within the cache
        if self.cache:
            cached_result = self.cache.get_item(url, params=params, headers=headers)
            if cached_result:
                return cached_result

        # add the parameters to the url, since the requests library converts special characters
        if session is None:
            session = self.get_session()
        if ssl is None:
            ssl = self.ssl

        url_buf = url
        if '?' not in url:
            url_buf += '?'
        for key, value in params.items():
            url_buf += f'{key}={value}&'
        url_buf = url_buf[:-1]

        while 1:
            result = session.request(method, url=url_buf, headers=headers, data=data, verify=ssl)
            if result.status_code != 200:
                if retries == 0:
                    return Response(status=result.status_code)
                retries -= 1
                sleep(retry_delay)
                continue
            else:
                response = Response(output=result.content, status=result.status_code)
                if self.cache:
                    self.cache.add_item(url, response, params=params, headers=headers)
                return response

    async def request_async(self, method: str,
                            url: str,
                            params: Optional[dict] = None,
                            headers: Optional[dict] = None,
                            data: Optional[dict] = None,
                            session: Optional[aiohttp.ClientSession] = None,
                            callback: Optional[dict] = None,
                            retries: int = 0,
                            retry_delay: Union[int, float] = 1,
                            ssl: Optional[bool] = None) -> Response:

        if session is None:
            session = await self.get_session_async()

        if self.cache:
            cached_result = await self.cache.get_item_async(url, params=params, headers=headers)
            if cached_result:
                if callback:
                    callback['response'] = cached_result
                return cached_result

        while 1:
            async with session.request(method, url, params=params, headers=headers, data=data, ssl=ssl) as resp:
                if resp.status != 200:
                    if retries == 0:
                        if callback:  # callback is only used for get_bulk_async
                            callback['response'] = Response(status=resp.status)
                        return Response(status=resp.status)
                    retries -= 1
                    if retry_delay:
                        await asyncio.sleep(retry_delay)
                    continue
                text_resp = await resp.text()
                response = Response(output=text_resp, status=resp.status)
                if callback:
                    callback['response'] = response
                if self.cache:
                    await self.cache.add_item_async(url, response, params=params, headers=headers)
            return response

    def request_bulk(self, method: str,
                     urls: list[str],
                     params: Optional[list[dict]] = None,
                     headers: Optional[list[dict]] = None,
                     data: Optional[list[dict]] = None,
                     session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
                     max_connections: int = 10,
                     per: int = 0.01,
                     retries: int = 0,
                     retry_delay: Union[int, float] = 1,
                     use_async: Optional[bool] = None,
                     ssl: Optional[bool] = None) -> list[Response]:
        """
        Request many urls at once
        :param method: HTTP method
        :param urls: A list of Urls
        :param params: A list of parameters for each request
        :param headers: Additional headers for each request
        :param data: Payload for post/put
        :param session: an aiohttp.Session or requests.Session. Leave none for default session
        :param max_connections: Maximum amount of asyncronous/concurrent connections
        :param per: Amount of time between adding more connections
        :param retries: Amount of retries if a request returns a non-200 code
        :param retry_delay: Amount of time between retries (seconds)
        :param use_async: Whether to use async. Leave none for default
        :param ssl: Whether to certify with ssl or not
        :return: A list of Responses
        """
        urls = [self.validate_url(u) for u in urls]

        if use_async is None:
            use_async = self.use_async
        elif use_async != self.use_async:
            self.toggle_async()
        if ssl is None:
            ssl = self.ssl

        if use_async:
            return self.run_async(
                self.request_bulk_async(method, urls, params=params, headers=headers, data=data, session=session,
                                        max_connections=max_connections, per=per, retries=retries,
                                        retry_delay=retry_delay,
                                        ssl=ssl))
        else:
            return self.request_bulk_sync(method, urls, params=params, headers=headers, data=data, session=session,
                                          retries=retries, retry_delay=retry_delay, ssl=ssl)

    def request_bulk_sync(self, method: str,
                          urls: list[str],
                          params: Optional[list[dict]] = None,
                          headers: Optional[list[dict]] = None,
                          data: Optional[list[dict]] = None,
                          session: Optional[requests.Session] = None,
                          retries: int = 0,
                          retry_delay: Union[int, float] = 1,
                          ssl: Optional[bool] = None) -> list[Response]:
        responses = []

        if ssl is None:
            ssl = self.ssl
        for i in range(len(urls)):
            # If params or headers is set to None, just pass None as the param/header
            header = None
            param = None
            dt = None
            if params:
                param = params[i]
            if headers:
                header = headers[i]
            if data:
                dt = data[i]

            responses.append(self.request(method, urls[i], params=param, headers=header, data=dt, session=session,
                                          retries=retries, retry_delay=retry_delay, ssl=ssl))
        return responses

    async def request_bulk_async(self, method: str,
                                 urls: list[str],
                                 params: Optional[list[dict]] = None,
                                 headers: Optional[list[dict]] = None,
                                 data: Optional[list[dict]] = None,
                                 session: Optional[aiohttp.ClientSession] = None,
                                 max_connections: int = 10,
                                 per: int = 0.01,
                                 retries: int = 0,
                                 retry_delay: Union[int, float] = 1,
                                 ssl: Optional[bool] = None,
                                 ) -> list[Response]:

        task_callback = [{'response': 0} for _ in range(len(urls))]
        # The loop will throttle tasks and repeatedly add more when they finish
        while True:
            running_tasks = 0
            done_tasks = 0
            # Count the number of running tasks and done tasks
            for task in task_callback:
                if task['response'] == 1:
                    running_tasks += 1
                if isinstance(task['response'], Response):
                    done_tasks += 1
            if done_tasks == len(urls):
                # If the amount of done tasks are equal to the amount of tasks, you have completed all the tasks
                return [task['response'] for task in task_callback]
            for i in range(len(task_callback)):
                if task_callback[i]['response'] == 0:  # Note: 0 means that it hasn't been touched yet
                    if running_tasks < max_connections:
                        # Run the tasks if connections aren't at max_connections and it hasn't already been run
                        task_callback[i]['response'] = 1  # 1 means processing
                        header = None
                        param = None
                        dt = None
                        if params:
                            param = params[i]
                        if headers:
                            header = headers[i]
                        if data:
                            dt = data[i]
                        asyncio.create_task(
                            self.request_async(method, urls[i], param, header, data=dt, retries=retries, session=session,
                                               retry_delay=retry_delay, ssl=ssl, callback=task_callback[i], ))
                        running_tasks += 1
                    else:
                        break  # added as many tasks as we could
            await asyncio.sleep(per)  # give some time for the coroutines to run

    def get(self,
            url: str,
            params: Optional[dict] = None,
            headers: Optional[dict] = None,
            session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
            retries: int = 0,
            retry_delay: Union[int, float] = 1,
            use_async: Optional[bool] = None,
            ssl: Optional[bool] = None) -> Response:
        return self.request(METHOD_GET, url, params=params, headers=headers, session=session, retries=retries,
                            retry_delay=retry_delay, use_async=use_async, ssl=ssl)

    def get_bulk(self,
                 urls: list[str],
                 params: Optional[list[dict]] = None,
                 headers: Optional[list[dict]] = None,
                 session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
                 max_connections: int = 10,
                 per: Union[int, float] = 0.01,
                 retries: int = 0,
                 retry_delay: Union[int, float] = 1,
                 use_async: Optional[bool] = None,
                 ssl: Optional[bool] = None) -> list[Response]:
        return self.request_bulk(METHOD_GET, urls, params=params, headers=headers, session=session,
                                 max_connections=max_connections, per=per, retries=retries,
                                 retry_delay=retry_delay,
                                 use_async=use_async, ssl=ssl)

    def post(self,
             url: str,
             params: Optional[dict] = None,
             headers: Optional[dict] = None,
             data: Optional[dict] = None,
             session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
             retries: int = 0,
             retry_delay: Union[int, float] = 1,
             use_async: Optional[bool] = None,
             ssl: Optional[bool] = None) -> Response:
        return self.request(METHOD_POST, url, params=params, headers=headers, data=data, session=session,
                            retries=retries, retry_delay=retry_delay, use_async=use_async, ssl=ssl)

    def post_bulk(self,
                  urls: list[str],
                  params: Optional[list[dict]] = None,
                  headers: Optional[list[dict]] = None,
                  data: Optional[list[dict]] = None,
                  session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
                  max_connections: int = 10,
                  per: Union[int, float] = 0.01,
                  retries: int = 0,
                  retry_delay: Union[int, float] = 1,
                  use_async: Optional[bool] = None,
                  ssl: Optional[bool] = None) -> list[Response]:
        return self.request_bulk(METHOD_POST, urls, params=params, headers=headers, data=data, session=session,
                                 max_connections=max_connections,
                                 per=per, retries=retries, retry_delay=retry_delay, use_async=use_async, ssl=ssl)

    def head(self,
             url: str,
             params: Optional[dict] = None,
             headers: Optional[dict] = None,
             session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
             retries: int = 0,
             retry_delay: Union[int, float] = 1,
             use_async: Optional[bool] = None,
             ssl: Optional[bool] = None) -> Response:
        return self.request(METHOD_HEAD, url, params=params, headers=headers, session=session, retries=retries,
                            retry_delay=retry_delay, use_async=use_async, ssl=ssl)

    def head_bulk(self,
                  urls: list[str],
                  params: Optional[list[dict]] = None,
                  headers: Optional[list[dict]] = None,
                  session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
                  max_connections: int = 10,
                  per: Union[int, float] = 0.01,
                  retries: int = 0,
                  retry_delay: Union[int, float] = 1,
                  use_async: Optional[bool] = None,
                  ssl: Optional[bool] = None) -> list[Response]:
        return self.request_bulk(METHOD_HEAD, urls, params=params, headers=headers, session=session,
                                 max_connections=max_connections, per=per, retries=retries,
                                 retry_delay=retry_delay,
                                 use_async=use_async, ssl=ssl)

    def delete(self,
               url: str,
               params: Optional[dict] = None,
               headers: Optional[dict] = None,
               session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
               retries: int = 0,
               retry_delay: Union[int, float] = 1,
               use_async: Optional[bool] = None,
               ssl: Optional[bool] = None) -> Response:
        return self.request(METHOD_DELETE, url, params=params, headers=headers, session=session, retries=retries,
                            retry_delay=retry_delay, use_async=use_async, ssl=ssl)

    def delete_bulk(self,
                    urls: list[str],
                    params: Optional[list[dict]] = None,
                    headers: Optional[list[dict]] = None,
                    session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
                    max_connections: int = 10,
                    per: Union[int, float] = 0.01,
                    retries: int = 0,
                    retry_delay: Union[int, float] = 1,
                    use_async: Optional[bool] = None,
                    ssl: Optional[bool] = None) -> list[Response]:
        return self.request_bulk(METHOD_DELETE, urls, params=params, headers=headers, session=session,
                                 max_connections=max_connections, per=per, retries=retries,
                                 retry_delay=retry_delay,
                                 use_async=use_async, ssl=ssl)

    def put(self,
            url: str,
            params: Optional[dict] = None,
            headers: Optional[dict] = None,
            data: Optional[dict] = None,
            session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
            retries: int = 0,
            retry_delay: Union[int, float] = 1,
            use_async: Optional[bool] = None,
            ssl: Optional[bool] = None) -> Response:
        return self.request(METHOD_PUT, url, params=params, headers=headers, data=data, session=session,
                            retries=retries, retry_delay=retry_delay, use_async=use_async, ssl=ssl)

    def put_bulk(self,
                 urls: list[str],
                 params: Optional[list[dict]] = None,
                 headers: Optional[list[dict]] = None,
                 data: Optional[list[dict]] = None,
                 session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
                 max_connections: int = 10,
                 per: Union[int, float] = 0.01,
                 retries: int = 0,
                 retry_delay: Union[int, float] = 1,
                 use_async: Optional[bool] = None,
                 ssl: Optional[bool] = None) -> list[Response]:
        return self.request_bulk(METHOD_PUT, urls, params=params, headers=headers, data=data, session=session,
                                 max_connections=max_connections, per=per, retries=retries,
                                 retry_delay=retry_delay,
                                 use_async=use_async, ssl=ssl)

    def option(self,
               url: str,
               params: Optional[dict] = None,
               headers: Optional[dict] = None,
               session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
               retries: int = 0,
               retry_delay: Union[int, float] = 1,
               use_async: Optional[bool] = None,
               ssl: Optional[bool] = None) -> Response:
        return self.request(METHOD_OPTIONS, url, params=params, headers=headers, session=session, retries=retries,
                            retry_delay=retry_delay, use_async=use_async, ssl=ssl)

    def option_bulk(self,
                    urls: list[str],
                    params: Optional[list[dict]] = None,
                    headers: Optional[list[dict]] = None,
                    session: Optional[Union[requests.Session, aiohttp.ClientSession]] = None,
                    max_connections: int = 10,
                    per: Union[int, float] = 0.01,
                    retries: int = 0,
                    retry_delay: Union[int, float] = 1,
                    use_async: Optional[bool] = None,
                    ssl: Optional[bool] = None) -> list[Response]:
        return self.request_bulk(METHOD_OPTIONS, urls, params=params, headers=headers, session=session,
                                 max_connections=max_connections, per=per, retries=retries,
                                 retry_delay=retry_delay,
                                 use_async=use_async, ssl=ssl)

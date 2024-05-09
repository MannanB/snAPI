Basic Usage
===========

Getting Started
---------------

Start by creating an instance of the API. Specify the base URL of the API.

.. code-block:: python

    from SnAPI.api import API
    my_api = API("https://api.example.com/v1")

Adding Endpoints
----------------

After setting your key, you can add endpoints.

.. code-block:: python

    my_api.add_endpoint("/cat_names", "get_cat_names", method="GET") # https://api.example.com/v1/cat_names

Making Requests
---------------

.. code-block:: python

    response = my_api.get_cat_names() # returns a Response object

    print(response.json()) # parse JSON
    print(response.output) # print raw output
    print(response.status) # print status code
    print(response) # prints "Response(status)"

You can also pass parameters, headers, and other options to the request.
Adding data to the request will automatically change the request to a POST request and add the data to the body.
If you want to make a POST request without data, you have to explicitly set the method to "POST" when creating the endpoint.

.. code-block:: python

    response = my_api.get_cat_names(params={"limit": 5}) # https://api.example.com/v1/cat_names?limit=5

    response = my_api.request_endpoint("get_cat_names") # You can also call the endpoint explicitly

    response = my_api.get_cat_names(data={"name": "Fluffy"}) # POST request with data. 

    responses = my_api.get_cat_names(amount=20) # Will call the API 20 times

    params = [{"limit": 5}, {"limit": 10}, {"limit": 15}]
    responses = my_api.get_cat_names(params=params) # Will call the API with each parameter and return a list of responses

Note that SnAPI will try to infer the number of requests as best as possible.
For example, if you pass in a list of parameters and a single header, SnAPI will make a request for each parameter with the same header.

.. code-block:: python

    params = [{"limit": 5}, {"limit": 10}, {"limit": 15}]
    responses = my_api.get_cat_names(params=params, headers={"param": "value"}) # Will call the API with each parameter and the same header

The same works for endpoint names.

.. code-block:: python

    my_api.add_endpoint("/dog_names", "get_dog_names", method="GET") # https://api.example.com/v1/dog_names

    request_names = ["get_cat_names", "get_dog_names", "get_cat_names"]

    responses = my_api.request_endpoints(request_names) # Will call the API with each endpoint name. Returns a list of responses in order of the endpoint names

Making Asynchronous Requests
----------------------------

Asynchronous requests are seamless with SnAPI. Just enable async on the API object.
It uses the exact same API as synchronous requests, so you can easily switch between the two.

.. code-block:: python

    my_api.enable_async()
    response = my_api.get_cat_names(amount=20) # will call the API 20 times asynchronously

In order limit the connections, you can set the maximum number of connections at a times. This is useful if there is a rate limit on the API.

.. code-block:: python

    my_api.enable_async()
    response = my_api.get_cat_names(amount=20, max_conns=5) # will call the API 20 times asynchronously with a maximum of 5 connections at a time

Key Configuration
-----------------

Add a key for authentication if needed. Multiple authentication methods are supported.

Usage via URL parameters

.. code-block:: python

    from SnAPI.api import Key

    key = snapi.Key(name="key", key="value") # https://api.example.com/endpoint?key=value
    key = snapi.Key(my_key_name="my_key_value") # https://api.example.com/endpoint?my_key_name=my_key_value

    # key will be automatically applied to any endpoint requests
    my_api = API("https://api.example.com/v1", key=key)

Usage via headers

.. code-block:: python

    from SnAPI.api import Key
    import SnAPI

    key = snapi.Key(name="Authorization", key="Bearer my_token", key_type=SnAPI.HEADERS) # passes {"Authorization": "Bearer my_token"} in headers

Usage via HTTP auth

.. code-block:: python

    from SnAPI.api import Key
    import SnAPI

    key = snapi.Key(username="my_username", password="my_password") # key_type isn't needed as long as username/password is passed

Caching
-------

SnAPI supports caching to reduce the number of requests made to the API. This is useful for endpoints that don't change often.
In order to limit the size of the cache, you can set the maximum number of items to cache. There are multiple types of caching available.

- *First In First Out (FIFO)*: When cache is full, the oldest item is removed.
- *Least Recently Used (LRU)*: When cache is full, the least recently used item is removed.
- *Least Frequently Used (LFU)*: When cache is full, the least frequently used item is removed.
- *Most Recently Used (MRU)*: When cache is full, the most recently used item is removed.
- *Random Replacement (RR)*: When cache is full, a random item is removed.

By default the cache size is LRU with a maximum of 10 items. 

.. code-block:: python

    from SnAPI.cache import MemoryCache, FIFO, LRU, LFU, MRU, RR

    my_api = API("https://api.example.com/v1", use_cache=True) # create a cache with default settings

    my_api = API("https://api.example.com/v1", cache=MemoryCache(cache_policy=FIFO, max_size=5)) # create a cache with FIFO policy and a maximum of 5 items

    my_api = API("https://api.example.com/v1", cache=MemoryCache(cache_policy=LRU, max_size=5000)) # create a cache with LRU policy and a maximum of 5000 items

Currently there is only support for in-memory caching, but support for other types of caching will be added in the future.
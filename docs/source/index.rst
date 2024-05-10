Overview
==========

SnAPI is a framework for building restful API clients in Python. Its primary goals are to provide a simple, consistent interface for interacting with restful APIs, and to provide a way to easily extend the framework to support new APIs.

Why SnAPI?
----------

- **Flexible Authentication**: Supports various authentication methods easily configurable per request.
- **Asynchronous Support**: Built-in support for asynchronous operations making it ideal for I/O bound tasks.
- **Caching Mechanisms**: Integrated caching features help reduce latency and load, enhancing performance.
- **Easy Endpoint Management**: Simplify the addition and management of various API endpoints.

Sample Usage
------------
.. code-block:: python::

    from snapi import API

    api = API('http://api.example.com/v1')
    api.add_endpoint('/users', 'get_users')

    # GET /users
    output = api.get_users() # or api.request_endpoint(endpoint_name='get_users')
    print(output)


SnAPI adds a simple interface for implementing API keys as well. API Keys may be passed through request parameters, headers, or via HTTP auth.

.. code-block:: python::
    import snapi

    my_params_key = snapi.Key(name="key", key="value", key_type=snapi.PARAMS)
    my_headers_key = snapi.Key(name="key", key="value", key_type=snapi.HEADERS)
    my_auth_key = snapi.Key(username="user", password="pass") # Defaults to AUTH

    api = snapi.API('http://api.example.com/v1', key=my_params_key)

Asynchronous Requests are easily done by toggling async. This is ideal for making many requests at once.

.. code-block:: python::
    api = snapi.API('http://api.example.com/v1')
    api.add_endpoint('/search', 'search')

    api.toggle_async()

    queries = ['query1', 'query2', 'query3']

    api.search(amount=3, query=queries) # will return a list of responses

Asynchronous requests with rate limiting. The following will only allow a maximum of 2 connections to the API at once. This defaults to 10.

.. code-block:: python::
    api.search(amount=3, query=queries, max_conns=2) # will return a list of responses

.. toctree::
   :maxdepth: 2
   :caption: Contents

   basic_usage
   advanced_usage

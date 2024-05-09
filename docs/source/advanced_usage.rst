Advanced Usage
=============

Subclassing the API class
--------------------------

Creating a child class of the API class is a good way to implement your own custom progrmatic API for a specific WebAPI.
This is especially useful when the WebAPI provider doesn't have a Python SDK or the SDK is not up to date.

A great example can be seen here:
https://github.com/MannanB/snAPI/blob/main/examples/pubmed_example.py

.. code-block:: python

    from SnAPI.api import API

    class myApi(snapi.API):
        def __init__(self, my_key):
            super.__init__(key=snapi.Key(key=my_key))
            self.add_endpoint("endpoint", name="test")

        def analyze_test(self, text):
            result = self.test(text)

            # do some complex analysis here
            result = result + " analyzed"

            return result

    api = myApi("my_key")

    print(api.analyze_test("some text"))

This is a simple example, but you can see how you can easily extend the API class to create your own custom API.

Rotating Keys
-------------

If you want to rotate keys for any reason, you can do so by creating a new Key object with multiple keys.
This works exactly the same as the Key object with a single key, except you have to pass a list of string instead of a single string.

.. code-block:: python

    from SnAPI.api import API, Key

    key = Key(my_key_name=["key1", "key2", "key3"], n_uses_before_switch=50) # switch key every 50 uses

    api = API(key=key)


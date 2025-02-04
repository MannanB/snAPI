# snAPI
A library for seamlessly and asynchronously calling Web APIs

The purpose of the library is to get rid of any boilerplate that comes with requesting or caching any kind of web API.

Check out the docs [here](https://pysnapi.readthedocs.io/en/latest/basic_usage.html)

# Sample usage

```
import snAPI

dog_api = snAPI.API(key=snAPI.Key(api_key="very_secret123"))

# define an endpoint as myendpoint
dog_api.add_endpoint("https://dog.ceo/api/breeds/list/all", name="get_all_breeds")

result = myapi.get_all_breeds()

print(result.output)
```

# Sample usage with asyncronous and rate-limiting
```
import snAPI

myapi = snAPI.API()
myapi.add_endpoint("https://cat-fact.herokuapp.com/facts/", name="get_cat_fact")

myapi.enable_async()

# request 100 cat facts, but only allow 10 requests at a time
results = myapi.get_cat_fact(amount=100, max_conns=10)
```

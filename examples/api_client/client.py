import snapi


class MyAPIClient(snapi.API):
    def __init__(self, my_key):
        super.__init__(key=snapi.Key(key=my_key))
        self.add_endpoint("https://myapiurl.com/api/v1/get_names", name="get_names")
        self.add_endpoint("https://myapiurl.com/api/v1/add_name", name="add_name", method="POST")
        self.add_endpoint("https://myapiurl.com/api/v1/find_address", name="find_address")


api = MyAPIClient('apikey123')

print(api.get_names())
api.add_name(name="John")
api.add_name(name="Max")
print(api.get_names())


huge_name_list = ['John', 'Max', 'Alex', 'Bob', 'Alice', 'Jane', 'Jill', 'Jack']
api.toggle_async()

addresses = api.find_address(names=huge_name_list, max_conns=4)
print(addresses)

api.toggle_async()

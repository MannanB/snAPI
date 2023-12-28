import sys
sys.path.insert(0, r'C:\Users\manna\OneDrive\Documents\Python\snAPI\snAPI\src')

import snAPI

class MyAPIClient(snAPI.API):
    def __init__(self):
        super().__init__()
        self.add_endpoint("http://127.0.0.1:5000/get_names", endpoint_name="get_names")
        self.add_endpoint("http://127.0.0.1:5000/add_name", endpoint_name="add_name")

api = MyAPIClient()

print(api.get_names().output)
api.add_name(name="John")
api.add_name(name="Max")
print(api.get_names().output)

huge_name_list = ['John', 'Max', 'Alex', 'Bob', 'Alice', 'Jane', 'Jill', 'Jack']
api.enable_async()

api.add_name(amount=len(huge_name_list), name=huge_name_list)
print(api.get_names().output)

api.close()
import unittest
import threading
import test_api
import os

def run_test_api():
    test_api.app.run(debug=False)

test_api_thread = threading.Thread(target=run_test_api)
test_api_thread.start()

while 1:
    loader = unittest.TestLoader()
    start_dir = './'
    suite = loader.loadTestsFromNames(["test_caching", "test_api_client"])

    runner = unittest.TextTestRunner()
    runner.run(suite)
    input()
    os.system("clear")

test_api_thread.join()
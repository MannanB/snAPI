from flask import Flask, request
from flask_restful import Resource, Api, reqparse
import logging

app = Flask(__name__)
api = Api(app)

log = logging.getLogger('werkzeug')
log.disabled = True # change to false if u want logs

x = 0
key_counter = {}
retry_counter = 0


class Simple(Resource):
    def get(self):
        global x, key_counter
        parser = reqparse.RequestParser()

        parser.add_argument('key', required=True, location='args')
        parser.add_argument('q', required=False, location='args')

        args = parser.parse_args()  # parse arguments to dictionary
        if not (args["key"] in key_counter):
            key_counter[args["key"]] = 1
        else:
            key_counter[args["key"]] += 1
            x += 1

        return {'data': args['q']}


class Retry(Resource):
    def get(self):
        global retry_counter
        parser = reqparse.RequestParser()

        parser.add_argument('key', required=True, location='args')
        parser.add_argument('q', required=True, location='args')

        args = parser.parse_args()  # parse arguments to dictionary
        retry_counter += 1

        if retry_counter < 3:
            return {}, 429
        return {'data': args['q']}


class HeadersTest(Resource):
    def get(self):
        key = request.headers.get('key')
        return {'data': key}


api.add_resource(Simple, '/Simple')
api.add_resource(Retry, '/Retry')
api.add_resource(HeadersTest, '/HeadersTest')

if __name__ == '__main__':
    app.run(threaded=True, debug=True)  # run our Flask app

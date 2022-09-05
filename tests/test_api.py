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

        parser.add_argument('key', required=True)
        parser.add_argument('q', required=False)

        args = parser.parse_args()  # parse arguments to dictionary
        if not (args["key"] in key_counter):
            key_counter[args["key"]] = 1
        else:
            key_counter[args["key"]] += 1
        print(f'SIMPLE >> {args["q"]}:{args["key"]} at NUMBER {x}; {key_counter[args["key"]]} times')
        x += 1

        return {'data': args['q']}, 200


class Retry(Resource):
    def get(self):
        global retry_counter
        parser = reqparse.RequestParser()

        parser.add_argument('key', required=True)
        parser.add_argument('q', required=True)

        args = parser.parse_args()  # parse arguments to dictionary
        print(f'RETRY >> Im on retry {retry_counter}!')
        retry_counter += 1

        if retry_counter < 3:
            return {}, 429
        return {'data': args['q']}, 200


class HeadersTest(Resource):
    def get(self):
        key = request.headers.get('key')
        return {'data': key}, 200


api.add_resource(Simple, '/Simple')
api.add_resource(Retry, '/Retry')
api.add_resource(HeadersTest, '/HeadersTest')

if __name__ == '__main__':
    app.run()  # run our Flask app

from flask import Flask, request
from flask_restful import Resource, Api, reqparse
import logging

app = Flask(__name__)
api = Api(app)

log = logging.getLogger('werkzeug')
log.disabled = True  # change to false if u want logs

names = []

class GetNames(Resource):
    def get(self):
        global names
        return {'names': names}

class AddName(Resource):
    def get(self):
        global names
        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True, location='args')
        args = parser.parse_args()  # parse arguments to dictionary

        names.append(args['name'])
        return {'status': 'success'}


api.add_resource(GetNames, '/get_names')
api.add_resource(AddName, '/add_name')

if __name__ == '__main__':
    app.run()  # run our Flask app

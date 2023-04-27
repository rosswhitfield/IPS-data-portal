import os
from flask import Flask, jsonify, g, request
from pymongo import MongoClient
from werkzeug.local import LocalProxy


def get_db():
    if 'db' not in g:
        client = MongoClient(host=os.environ.get('MONGO_HOST', 'localhost'),
                             port=int(os.environ.get('MONGO_PORT', 27017)),
                             username=os.environ.get('MONGO_USERNAME'),
                             password=os.environ.get('MONGO_PASSWORD'))
        g.db = client.portal

    return g.db


db: LocalProxy = LocalProxy(get_db)


def create_app():
    # create and configure the app
    app = Flask(__name__)

    @app.route('/api/runs')
    def runs():
        runs = []

        for run in db.data.find(projection={'_id': False, "portal_runid": True}):
            runs.append(run['portal_runid'])

        return jsonify(runs), 200

    @app.route('/api/<string:portal_runid>')
    def data(portal_runid: str):
        return jsonify(db.data.find_one(
            {"portal_runid": portal_runid},
            projection={'_id': False})
                       ), 200

    @app.route('/api/<string:portal_runid>/timestamps')
    def timestamps(portal_runid: str):
        return jsonify(db.data.find_one(
            {"portal_runid": portal_runid},
            projection={'_id': False, 'timestamps': True}
        )['timestamps']), 200

    @app.route('/api/<string:portal_runid>/<string:timestamp>')
    def timestamp(portal_runid: str, timestamp: str):
        return jsonify(db.data.find_one(
            {"portal_runid": portal_runid},
            projection={'_id': False, f'data.{timestamp}': True}
        )['data'][timestamp]), 200

    @app.route('/api/<string:portal_runid>/<string:timestamp>/parameters')
    def parameters(portal_runid: str, timestamp: str):
        return jsonify(list(db.data.find_one(
            {"portal_runid": portal_runid},
            projection={'_id': False, f'data.{timestamp}': True}
        )['data'][timestamp].keys())), 200

    @app.route('/api/<string:portal_runid>/<string:timestamp>/<string:parameter>')
    def parameter(portal_runid: str, timestamp: str, parameter: str):
        return jsonify(db.data.find_one(
            {"portal_runid": portal_runid},
            projection={'_id': False, f'data.{timestamp}.{parameter}': True}
        )['data'][timestamp][parameter]), 200

    @app.route('/api/add', methods=['POST'])
    def add():
        data = request.get_json()

        db.data.update_one({"portal_runid": data['portal_runid']},
                           {
                               "$push": {"timestamps": data['timestamp']},
                               "$set": {f"data.{data['timestamp']}": data['data']}
                           },
                           upsert=True
                           )

        return jsonify("success"), 200

    @app.route('/api/query', methods=['POST'])
    def query():
        return jsonify(sorted(x['portal_runid']
                              for x in db.data.find(
                                      request.get_json(),
                                      projection={'_id': False, "portal_runid": True}
                              ))), 200

    return app

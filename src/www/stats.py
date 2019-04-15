#!/bin/python3
# author: Jan Hybs


import flask.json
from database.mongo import Mongo
import json


def register_routes(app, socketio):
    @app.route('/stats')
    def stats():
        mongo = Mongo()
        # for d in mongo.last_n_correct_results(user_id='jan.hybs'):
        #     print(d['result']['status'] == 'answer-correct')
        #
        # print('')
        # for d in mongo.last_n_wrong_results(user_id='jan.hybs'):
        #     print(d['result']['status'] == 'answer-correct')
        #
        # print('')
        items = list(mongo.last_n_results_from_students())
        return flask.json.dumps(items)
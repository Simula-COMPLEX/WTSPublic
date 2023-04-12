"""
Created on March 07, 2023

@author: Hassan Sartaj
@version: 1.0
"""
import time
import random

import pandas as pd
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
import logging
import requests

# creating the flask app
app = Flask(__name__.split('.')[0])
# creating an API object
api = Api(app)
# DTs map
_dts_map = None
dt2pt_map = {}


class Device(Resource):
    # handling get requests
    def get(self, num):
        global _dts_map, dt2pt_map
        if str(num) not in _dts_map.keys():
            response = {'Error': "No data available for " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            model_ins = _dts_map[str(num)]
            response = model_ins.get_target_data(__class__.__name__)
            logging.info("[APD-DT] Received instance data {}".format(response))
            if __class__.__name__ in dt2pt_map.keys():
                logging.info("[APD-DT] Sending request to PTServer")
                # TODO: need to uncomment whenever communicating with PD
                # [res, time_device, httpcode_device] = send_request("get", dt2pt_map[__class__.__name__], "")
                # logging.info("[APD-DT] Received response from PTServer: {}".format(res))
            if len(response) == 0:
                response['Error'] = "No data available for " + __class__.__name__ + " # " + str(num)
                return response, 503
            else:
                return response, 200

    # handling post requests
    def post(self, num):
        global _dts_map
        logging.info("[DTServer] Processing request")
        # for time sync
        time.sleep(random.uniform(1.5, 3.9))
        if str(num) not in _dts_map.keys():
            response = {'Error': "Cannot find " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            data = request.get_json()
            logging.info("[DTServer] Received data: {}".format(data))
            model_ins = _dts_map[str(num)]
            errors = model_ins.update_instance_model(data)
            if len(errors) > 0:
                return errors, 503
            else:
                response = {'Success': __class__.__name__ + " data updated!"}
                return response, 200

    # handling put requests
    def put(self, num):
        global _dts_map
        logging.info("[DTServer] Processing request")
        # for time sync
        time.sleep(random.uniform(1.5, 3.9))
        if str(num) not in _dts_map.keys():
            response = {'Error': "Cannot find " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            data = request.get_json()
            logging.info("[DTServer] Received data: {}".format(data))
            model_ins = _dts_map[str(num)]
            errors = model_ins.update_instance_model(data)
            if len(errors) > 0:
                return errors, 503
            else:
                response = {'Success': __class__.__name__ + " data updated!"}
                return response, 200


class Setting(Resource):
    def get(self, num):
        global _dts_map
        if _dts_map is None or str(num) not in _dts_map.keys():
            response = {'Error': "No data available for " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            model_ins = _dts_map[str(num)]
            response = model_ins.get_target_data(__class__.__name__)
            logging.info("[APD-DT] Received instance data {}".format(response))
            if len(response) == 0:
                response['Error'] = "No data available for " + __class__.__name__ + " # " + str(num)
                return response, 503
            else:
                return response, 200

    # handling post requests
    def post(self, num):
        logging.info("[DTServer] Processing request")
        # for time sync
        time.sleep(random.uniform(1.5, 3.9))
        global _dts_map
        if str(num) not in _dts_map.keys():
            response = {'Error': "Cannot find " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            data = request.get_json()
            logging.info("[DTServer] Received data: {}".format(data))
            model_ins = _dts_map[str(num)]
            errors, d_count, e_count = model_ins.update_instance_model(data)
            if len(errors) > 0:
                if (d_count/e_count) < 2:
                    return errors, 200
                else:
                    return errors, 503
            else:
                response = {'Success': __class__.__name__ + " data updated!"}
                return response, 200

    # handling put requests
    def put(self, num):
        global _dts_map
        logging.info("[DTServer] Processing request")
        # for time sync
        time.sleep(random.uniform(1.5, 3.9))
        if str(num) not in _dts_map.keys():
            response = {'Error': "Cannot find " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            data = request.get_json()
            logging.info("[DTServer] Received data: {}".format(data))
            model_ins = _dts_map[str(num)]
            errors = model_ins.update_instance_model(data)
            if len(errors) > 0:
                return errors, 503
            else:
                response = {'Success': __class__.__name__ + " data updated!"}
                return response, 200


class MedicationPlan(Resource):
    def get(self, num):
        global _dts_map
        if _dts_map is None or str(num) not in _dts_map.keys():
            response = {'Error': "No data available for " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            model_ins = _dts_map[str(num)]
            response = model_ins.get_target_data(__class__.__name__)
            logging.info("[APD-DT] Received instance data {}".format(response))
            if len(response) == 0:
                response['Error'] = "No data available for " + __class__.__name__ + " # " + str(num)
                return response, 503
            else:
                return response, 200

    # handling post requests
    def post(self, num):
        global _dts_map
        logging.info("[DTServer] Processing request")
        # for time sync
        time.sleep(random.uniform(1.5, 3.9))
        if str(num) not in _dts_map.keys():
            response = {'Error': "Cannot find " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            data = request.get_json()
            logging.info("[DTServer] Received data: {}".format(data))
            model_ins = _dts_map[str(num)]
            errors = model_ins.update_instance_model(data)
            if len(errors) > 0:
                return errors, 503
            else:
                response = {'Success': __class__.__name__ + " data updated!"}
                return response, 200

    # handling put requests
    def put(self, num):
        global _dts_map
        logging.info("[DTServer] Processing request")
        # for time sync
        time.sleep(random.uniform(1.5, 3.9))
        if str(num) not in _dts_map.keys():
            response = {'Error': "Cannot find " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            data = request.get_json()
            logging.info("[DTServer] Received data: {}".format(data))
            model_ins = _dts_map[str(num)]
            errors = model_ins.update_instance_model(data)
            if len(errors) > 0:
                return errors, 503
            else:
                response = {'Success': __class__.__name__ + " data updated!"}
                return response, 200

    def delete(self, num):
        logging.info("[DTServer] Processing request")
        # for time sync
        time.sleep(random.uniform(1.5, 3.9))
        # todo: may need plan id to delete a specific plan
        response = {'Success': "Medication plan is removed!"}
        return response, 200


class Manage(Resource):
    def get(self, num):
        global _dts_map
        if _dts_map is None or str(num) not in _dts_map.keys():
            response = {'Error': "No data available for " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            model_ins = _dts_map[str(num)]
            response = model_ins.get_target_data(__class__.__name__)
            logging.info("[APD-DT] Received instance data {}".format(response))
            if len(response) == 0:
                response['Error'] = "No data available for " + __class__.__name__ + " # " + str(num)
                return response, 503
            else:
                return response, 200

    # handling post requests
    def post(self, num):
        global _dts_map
        logging.info("[DTServer] Processing request")
        # for time sync
        time.sleep(random.uniform(1.5, 3.9))
        if str(num) not in _dts_map.keys():
            response = {'Error': "Cannot find " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            data = request.get_json()
            logging.info("[DTServer] Received data: {}".format(data))
            model_ins = _dts_map[str(num)]
            model_ins.update_instance_model(data)
            response = {'Success': __class__.__name__ + " data updated!"}
            return response, 200

    # handling put requests
    def put(self, num):
        global _dts_map
        logging.info("[DTServer] Processing request")
        # for time sync
        time.sleep(random.uniform(1.5, 3.9))
        if str(num) not in _dts_map.keys():
            response = {'Error': "Cannot find " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            data = request.get_json()
            logging.info("[DTServer] Received data: {}".format(data))
            model_ins = _dts_map[str(num)]
            model_ins.update_instance_model(data)
            response = {'Success': __class__.__name__ + " data modified!"}
            return response, 200


class Cartridge(Resource):
    def get(self, num):
        global _dts_map
        if _dts_map is None or str(num) not in _dts_map.keys():
            response = {'Error': "No data available for " + __class__.__name__ + " # " + str(num)}
            return response, 503
        else:
            model_ins = _dts_map[str(num)]
            response = model_ins.get_target_data(__class__.__name__)
            logging.info("[APD-DT] Received instance data {}".format(response))
            if len(response) == 0:
                response['Error'] = "No data available for " + __class__.__name__ + " # " + str(num)
                return response, 503
            else:
                return response, 200


class DTServer:
    @staticmethod
    def init_server(mapping_file, dts_map):
        logging.info("[APD-DT] Initializing DT APIs")
        global _dts_map, dt2pt_map
        _dts_map = dts_map

        mapping = pd.read_table(mapping_file, delimiter=';')
        resources = [Device, Setting, MedicationPlan, Manage, Cartridge]
        # adding the defined resources along with their corresponding urls
        logging.debug("Mapping file content")
        # mapping links for SUT, DT, and PD
        for i, row in mapping.iterrows():
            model_elem = row['Model']
            dt_api = row['DT-API']
            device_api = row['Device-API']
            dt2pt_map[model_elem] = device_api
            logging.debug("{}".format(model_elem) + " - {}".format(dt_api) + " - {}".format(device_api))
            for res in resources:
                if res.__name__ == model_elem:
                    api.add_resource(res, dt_api)


    @staticmethod
    def start_server(host, port):
        logging.info("[APD-DT] Starting DT API server at host:: {}".format(host) + " - port:: {}".format(str(port)))
        from waitress import serve
        serve(app, host=host, port=port)
        app.run(debug=True)


def send_request(method, base_url, act_api, json_option=None):
    url = base_url + act_api
    with requests.Session() as s:
        if method == 'get':
            response = s.get(url, params=json_option)
        else:
            response = s.post(url=url, json=json_option)
        logging.info("Response time: {}".format(response.elapsed))
        logging.info("Status code: {}".format(response.status_code))
        return response.json(), response.elapsed.total_seconds(), response.status_code

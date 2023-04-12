"""
Created on March 06, 2023

@author: Hassan Sartaj
@version: 1.0
"""
import logging
import time

from commons.configs import ConfigLoader
from dtmodeler.evaluator import ConstraintsEvaluator
from dtmodeler.model2json import load_model, save_model_in_json, get_model_map
from dtsimulator.dtserver import DTServer
from dtsimulator.edtmodel import ModelInstance


# configs
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

model_dir = "models/"
model_file = model_dir + "apd_mm.ecore"
out_dir = "outputs/"
inp_dir = "inputs/"

if __name__ == '__main__':
    inp_path = inp_dir + "device.json"
    t_inp_path = inp_dir + "device-t2.json"
    config_file = inp_dir + "config.ini"
    sm_file = inp_dir + "sm-apd.xmi"
    snippets_file = inp_dir + "snippets.ini"
    mapping_file = inp_dir + "mapping.csv"

    dts_map = {}
    ConfigLoader.load_configs(file=config_file)
    # load metamodel
    model_root = load_model(model_path=model_file)
    # save metamodel in json for input
    save_model_in_json(out_path=inp_path)
    model_map = get_model_map()

    # TODO: uncomment for demo
    # logging.info("[APD-DT] Please provide initial device settings in 'inputs/device.json' file")
    # input("[APD-DT] Press any key to continue")

    # get the settings from device.json and create model instance
    # ==> for one instance
    model_ins = ModelInstance(instance_num=1, input_path=t_inp_path, out_path=out_dir, model_map=model_map, sm_file=sm_file, snippets_file=snippets_file)
    ConstraintsEvaluator.load_constraints(model_root=model_root)
    # create device instance model
    ins_path = model_ins.create_instance_model()
    if type(ins_path) == dict:
        logging.info("[APD-DT] ERRORS: {}".format(ins_path))
    else:
        logging.info("[APD-DT] Instance path: {}".format(ins_path))
        dts_map[model_ins.get_device_number()] = model_ins


    # start the DT API server
    DTServer.init_server(mapping_file=mapping_file, dts_map=dts_map)
    # DTServer.start_server(host="0.0.0.0", port=7000)
    DTServer.start_server(host=ConfigLoader.get_dtserver_host(), port=ConfigLoader.get_dtserver_port())



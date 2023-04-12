"""
Created on March 06, 2023

@author: Hassan Sartaj
@version: 1.0
"""

from pyecore.resources import ResourceSet, URI
import pyecore.behavior  # This import adds the behavior decorator to EClass
# import pyecore.type as xmltypes  # for loading XML types
from pyecore.ecore import EClass
import json
import logging


root_clas = None
model_root = None


def load_model(model_path):
    global model_root
    # Read the metamodel first
    rset = ResourceSet()
    model_root = rset.get_resource(URI(model_path)).contents[0]
    # Register the metamodel (in case we open an XMI model later)
    rset.metamodel_registry[model_root.nsURI] = model_root
    logging.info(f"[APD-DT] Model '{model_root.name}' loaded")
    return model_root


def get_model_map():
    model_map = {}
    classifiers = model_root.eClassifiers
    for clas in classifiers.items:
        if type(clas) is pyecore.ecore.EClass:
            model_map[clas.name] = clas.eAttributes
    return model_map


def get_model_dict():
    global root_clas, model_root
    # reading model elements
    classifiers = model_root.eClassifiers
    model_dict = {}
    new_model_dict = {}
    # first pass for classes
    for clas in classifiers.items:
        if type(clas) is pyecore.ecore.EClass:
            logging.debug("-> Class: {}".format(clas.name))
            attr_dict = get_class_attributes(clas)
            model_dict[clas.name] = attr_dict
            if len(clas.eReferences) > 2:
                # root_clas = clas.name
                count = 0
                for cref in clas.eReferences:
                    if cref.containment:
                        count += 1
                if count == len(clas.eReferences):
                    root_clas = clas.name
                    logging.debug("-> Root class: {}".format(root_clas))

    # second pass for relationships of classes
    for clas in classifiers.items:
        if type(clas) is pyecore.ecore.EClass:
            if len(clas.eReferences) > 0:
                traverse_ref_classifiers(clas, model_dict[clas.name])

    new_model_dict[root_clas] = model_dict[root_clas]
    return new_model_dict


def traverse_ref_classifiers(clas, model_dict):
    if len(clas.eReferences) > 0:
        for c_ref in clas.eReferences:
            # populate containing class attributes
            ref_clas = c_ref.eType
            attr_dict = get_class_attributes(ref_clas)
            model_dict[ref_clas.name] = attr_dict
            traverse_ref_classifiers(ref_clas, model_dict[ref_clas.name])


def get_class_attributes(clas):
    attr_dict = {}
    # reading class attributes
    for attr in clas.eAttributes:
        logging.debug("-> Attribute name: {}".format(attr.name) + " - type: {}".format(attr.eType.name))
        attr_dict[attr.name] = ""

    return attr_dict


def save_model_in_json(out_path):
    model_dict = get_model_dict()
    logging.debug("-> model_dict: {}".format(model_dict))
    # Serializing json object
    json_object = json.dumps(model_dict, indent=4)
    # Writing to json object to file
    with open(out_path, "w") as outfile:
        outfile.write(json_object)


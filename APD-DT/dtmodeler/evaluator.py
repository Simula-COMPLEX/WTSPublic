"""
Created on March 06, 2023

@author: Hassan Sartaj
@version: 1.0
"""

import ast
import pyecore
import logging


class ConstraintsEvaluator:
    __constraints_map = {}

    @staticmethod
    def load_constraints(model_root):
        classifiers = model_root.eClassifiers
        logging.info("[APD-DT] Loading metamodel constraints")
        for clas in classifiers.items:
            all_keys = []
            constraints = []
            logging.debug("==> Classifier:: {}".format(clas.name))
            if type(clas) is pyecore.ecore.EClass:
                # reading class constraints inside annotations
                for an in clas.eAnnotations:
                    if 'constraints' in an.details:
                        inv_names = an.details['constraints']
                        for inm in inv_names.split(" "):
                            all_keys.append(inm)
                    for ak in all_keys:
                        if ak in an.details:
                            logging.debug("==> Inv name: {}".format(ak) + " - condition: {}".format(an.details[ak]))
                            constraints.append(an.details[ak])
                ConstraintsEvaluator.__constraints_map[clas.name] = constraints
        logging.debug("==> ConstraintsEvaluator - constraints_map\n".format(ConstraintsEvaluator.__constraints_map))

    @staticmethod
    def get_constraints(clas):
        if clas not in ConstraintsEvaluator.__constraints_map:
            logging.info("[APD-DT] Class {}".format(clas) + " no constraints!")
        else:
            return ConstraintsEvaluator.__constraints_map[clas]

    @staticmethod
    def evaluate_constraint(constraint, attribute, value):
        if type(value) is str:
            str_value = "\"" + value + "\""
            exp = ast.parse(attribute + "=" + str_value)
        else:
            exp = ast.parse(attribute + "=" + str(value))

        logging.debug("==> parsing: {}".format(attribute) + "={}".format(str(value)))
        logging.debug("==> evaluating: {}".format(constraint))
        exec(compile(exp, filename="<ast>", mode="exec"))
        return eval(constraint)

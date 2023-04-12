"""
Created on March 07, 2023

@author: Hassan Sartaj
@version: 1.0
"""
import threading
from threading import Thread
import configparser
from pyecore.resources import ResourceSet, URI
import pyecore.behavior  # This import adds the behavior decorator to EClass
import pyecore.behavior as behavior
from pyecore.utils import DynamicEPackage
import pyecore.type as xmltypes  # for loading XML types
from pyecore.ecore import EClass
from pyecore.resources.xmi import XMIResource
import datetime, json, time, logging
from dtmodeler.evaluator import ConstraintsEvaluator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from queue import Queue


try:
    import asyncio
except ImportError:
    import trollius as asyncio

keys = []
flat_dict = {}
rset = ResourceSet()
# TODO: can change fixed model path
model_root = rset.get_resource(URI("models/apd_mm.ecore")).contents[0]
is_updated = False
results = {}


class ModelInstance:
    def __init__(self, instance_num=1, input_path=None, out_path=None, model_map=None, sm_file=None,
                 snippets_file=None):
        self.model_map = model_map
        self.instance_num = instance_num
        self.json_input = input_path
        self.apd_sm = sm_file
        self.sm_snippets = snippets_file
        if out_path is not None:
            self.ins_name = out_path + "apd_ins_" + str(self.instance_num) + ".xmi"
        else:
            self.ins_name = "apd_ins_" + str(self.instance_num) + ".xmi"
        self.class_ins_map = {}
        self.enums = {}
        self.root_clas = None
        self.all_clas_instances = []
        self.device_num = None
        self.clas_attribute_map = {}
        self.clas_ref_map = {}

        queue = Queue()
        self.observer = ObserverThread(queue)
        self.observer.start()
        self.dt = None

    # load data from json model file
    def __load_json_file(self):
        if self.json_input is None:
            raise Exception("Path to JSON input file is none!")
        else:
            json_file = open(self.json_input)
            data = json.load(json_file)
            json_file.close()
            return data

    # flatten json data
    def __flatten_data(self, d):
        for k in d.keys():
            if k not in keys:
                if type(d[k]) is dict:
                    keys.append(k)
                    flat_dict[k] = {}
                    self.__flatten_data(d[k])
                elif type(d[k]) is str:
                    if len(flat_dict[keys[len(keys) - 1]]) == 0:
                        flat_dict[keys[len(keys) - 1]] = {}
                    flat_dict[keys[len(keys) - 1]][k] = d[k]

    def __get_multiple_keys(self, clas, model_map):
        multi_keys = []
        if clas not in model_map.keys():
            for k in model_map.keys():
                if "-" in k:
                    if k.split("-")[0] == clas:
                        multi_keys.append(k)
        return multi_keys

    # for saving last state of the device
    def __save_model(self, clas_instances):
        xmi_rset = ResourceSet()
        xmi_resource = xmi_rset.create_resource(URI(self.ins_name))
        for clas_ins in clas_instances:
            if type(clas_ins) is list:
                for ci in clas_ins:
                    xmi_resource.append(ci)
            else:
                xmi_resource.append(clas_ins)
        logging.info("[APD-DT] Saving instance model snapshot...")
        xmi_resource.save()

    def __set_attribute_value(self, at, value, constraints, clas_ins, evaluated):
        logging.debug("attribute: {}".format(at.name) + " - value: {}".format(value))
        result = {}
        if at.eType.name == 'EInt' or at.eType.name == 'ELong':
            eval_res = None
            for constraint in constraints:
                if at.name in constraint:
                    try:
                        eval_res = ConstraintsEvaluator.evaluate_constraint(constraint, at.name, int(value))
                        logging.debug("eval_res: {}".format(eval_res))
                        break
                    except ValueError:
                        eval_res = False
                        break

            if eval_res is None:  # no constraint to evaluate
                clas_ins.__setattr__(at.name, int(value))
            else:
                if eval_res:
                    clas_ins.__setattr__(at.name, int(value))
                else:
                    result[at.name] = "Validation Failed: Out of range value!"
                    logging.error("ERROR! Value mismatch.")
        elif at.eType.name == 'EString':
            eval_res = None
            for constraint in constraints:
                if at.name in constraint and constraint not in evaluated:
                    # transforming and checking null constraints
                    if "<>" in constraint and "null" in constraint:
                        constraint_1 = at.name + " or not " + at.name + ".isspace()"
                        eval_res = ConstraintsEvaluator.evaluate_constraint(constraint_1, at.name, str(value))
                        evaluated.append(constraint)
                        logging.debug("eval_res: {}".format(eval_res))
                        break
            if eval_res is None:  # no constraint to evaluate
                clas_ins.__setattr__(at.name, str(value))
            else:
                if eval_res:
                    clas_ins.__setattr__(at.name, value)
                else:
                    result[at.name] = "Validation Failed: Value cannot be null or empty!"
                    logging.error("ERROR! Value mismatch.")
        elif at.eType.name == 'EBoolean':
            eval_res = None
            for constraint in constraints:
                if at.name in constraint and constraint not in evaluated:
                    constraint_1 = constraint.replace("=", "==").replace("true", "True").replace("false",
                                                                                                 "False")
                    eval_res = ConstraintsEvaluator.evaluate_constraint(constraint_1, at.name, eval(value))
                    evaluated.append(constraint)
                    logging.debug("eval_res: {}".format(eval_res))
                    break
            if eval_res is None:  # no constraint to evaluate
                if type(value) != bool:
                    if value != " ":
                        clas_ins.__setattr__(at.name, eval(value.title()))
                else:
                    clas_ins.__setattr__(at.name, value)
            else:
                if eval_res:
                    if type(value) != bool:
                        if value != " ":
                            clas_ins.__setattr__(at.name, eval(value.title()))
                    else:
                        clas_ins.__setattr__(at.name, value)
                else:
                    result[at.name] = "Validation Failed: Expected boolean value!"
                    logging.error("ERROR! Value mismatch.")
        # checking for date and time formats
        elif at.eType.name == 'Date':
            try:
                date = datetime.datetime.strptime(value, '%Y-%m-%d').date()
                clas_ins.__setattr__(at.name, date)
            except:
                result[at.name] = "Validation Failed: Incorrect date/format!"
                logging.error("ERROR! Incorrect date/format!")
        elif at.eType.name == 'Time':
            try:
                time = datetime.datetime.strptime(value, '%H:%M:%S').time()
                clas_ins.__setattr__(at.name, time)
            except:
                result[at.name] = "Validation Failed: Incorrect time/format!"
                logging.error("ERROR! Incorrect time/format!")
        elif at.eType.name in self.enums.keys():  # check for enums
            found = False
            for k in self.enums.keys():
                if k == at.eType.name:
                    lits = self.enums[k]
                    for lit in lits:
                        if lit.name == value:
                            clas_ins.__setattr__(at.name, lit)
                            found = True
            if not found:
                result[at.name] = "Validation Failed: Value '" + str(value) + "' not found!"
                logging.error("ERROR! value {}".format(value) + " not found.")
        else:
            result[at.name] = "Validation Failed: Incorrect value type!"
            logging.error("Unsupported type!")

        return result

    def __create_class_ref_map(self, clas):
        # global _clas_ref_map
        clas_refs = []
        if len(clas.eReferences) > 0:
            count = 0
            for cref in clas.eReferences:
                if cref.containment and len(clas.eReferences) > 2:
                    count += 1
                clas_refs.append(cref.eType.name)
            if count > 0 and count == len(clas.eReferences):
                self.root_clas = clas.name
                logging.debug("Root class: {}".format(self.root_clas))
        if len(clas_refs) > 0:
            self.clas_ref_map[clas.name] = clas_refs

    def __create_class_instance(self, clas, attr_values, constraints, ins_num):
        ins_name = clas.name.lower() + "_ins_" + str(ins_num)
        clas_ins = clas(name=ins_name)
        logging.debug("- created instance: {}".format(clas_ins.name))
        self.__create_class_ref_map(clas)
        evaluated = []
        attributes = []
        results = []
        for at in clas.eAttributes:
            value = attr_values[at.name]
            if self.root_clas == clas.name and self.device_num is None:
                self.device_num = attr_values['number']
            result = self.__set_attribute_value(at, value, constraints, clas_ins, evaluated)
            if len(result) > 0:
                results.append(result)
            attributes.append(at.name)
        self.clas_attribute_map[clas.name] = attributes
        if len(results) > 0:
            return results
        else:
            return clas_ins

    def create_instance_model(self):
        global flat_dict, model_root
        logging.info("[APD-DT] Creating instance model with input settings")
        errors = {}
        data = self.__load_json_file()
        self.__flatten_data(data)
        classifiers = model_root.eClassifiers
        # create enums dict
        for clas in classifiers.items:
            if type(clas) is pyecore.ecore.EEnum:
                literals = list(clas.eLiterals)
                self.enums[clas.name] = literals
        # create class instance and set values to their attributes
        for clas in classifiers.items:
            logging.debug("Classifier:: {}".format(clas.name))
            if type(clas) is pyecore.ecore.EClass:
                constraints = ConstraintsEvaluator.get_constraints(clas.name)
                multi_keys = self.__get_multiple_keys(clas.name, flat_dict)
                clas_instances = []
                ins_num = 1
                if len(multi_keys) > 0:
                    for mk in multi_keys:
                        attr_values = flat_dict[mk]
                        clas_ins = self.__create_class_instance(clas, attr_values, constraints, ins_num)
                        if type(clas_ins) == list:
                            errors[clas.name] = clas_ins
                        else:
                            clas_instances.append(clas_ins)
                            self.all_clas_instances.append(clas_ins)
                        ins_num += 1

                else:
                    attr_values = flat_dict[clas.name]
                    clas_ins = self.__create_class_instance(clas, attr_values, constraints, ins_num)
                    if type(clas_ins) == list:
                        errors[clas.name] = clas_ins
                    else:
                        clas_instances.append(clas_ins)
                        self.all_clas_instances.append(clas_ins)

                if len(errors) == 0:
                    self.class_ins_map[clas.name] = clas_instances

        if len(errors) > 0:
            return errors
        else:
            self.__save_model(self.all_clas_instances)

            # run as a thread
            self.dt = self.DTBehavior(self.ins_name, self.root_clas, self.class_ins_map, self.clas_ref_map,
                                      self.model_map, self.apd_sm, self.sm_snippets)
            self.dt.start()
            return self.ins_name

    def update_instance_model(self, data):
        logging.info("[APD-DT] Received data: {} ".format(data))
        logging.info("[APD-DT] Updating instance model with input settings")
        d_count = 0
        e_count = 0
        errors = {}
        i = 0
        prev_k = ""
        is_plan_updated = False
        for dk in data.keys():
            if dk not in self.model_map.keys():
                clas = dk.split("-")[0]
                multiple = True
                if prev_k != clas:
                    prev_k = clas
                    i = 0
            else:
                clas = dk
                multiple = False

            if 'plan' in clas.lower():
                is_plan_updated = True
            attributes = self.model_map[clas]
            clas_ins = self.class_ins_map[clas]
            constraints = ConstraintsEvaluator.get_constraints(clas)
            results = []
            for attribute in data[dk].keys():
                evaluated = []
                for at in attributes:
                    if attribute == at.name:
                        value = data[dk][attribute]
                        # TODO: need to handle nested structure
                        d_count += 1
                        result = self.__set_attribute_value(at, value, constraints, clas_ins[i], evaluated)
                        if len(result) > 0:
                            results.append(result)
            if len(results) > 0:
                errors[clas] = results
                e_count += len(results)
            if multiple:
                i += 1
        if len(errors) > 0:
            # reset instance model to initial values #TODO: need to recheck
            self.create_instance_model()
            return errors, d_count, e_count
        else:
            if is_plan_updated:
                self.observer.queue.put(is_plan_updated)
            self.__save_model(self.class_ins_map.values())
            return {}

    def get_device_number(self):
        return self.device_num

    def get_all_instances(self):
        return self.all_clas_instances

    def __populate_data(self, target, res_map):
        clas_instances = self.class_ins_map[target]
        for clas_ins in clas_instances:
            values_dict = {}
            for attribute in self.clas_attribute_map[target]:
                values_dict[attribute] = str(clas_ins.eGet(attribute))
            res_map[clas_ins.name] = values_dict

    def __populate_target_data(self, target, res_map):
        if target in self.clas_ref_map.keys():
            self.__populate_data(target, res_map)
            for clas in self.clas_ref_map[target]:
                if clas in self.class_ins_map.keys():
                    self.__populate_target_data(clas, res_map)
                    self.__populate_data(clas, res_map)
            logging.info("Target '{}' ".format(target))
        elif target in self.class_ins_map.keys():
            self.__populate_data(target, res_map)
            logging.info("Target '{}' ".format(target))
        elif target == "Manage":
            self.__populate_data(self.root_clas, res_map)
            logging.info("Target '{}' ".format(target))
        else:
            # results['Error'] = "No data available for "+target
            logging.info("Target '{}' not found.".format(target))

    def get_target_data(self, target):
        global results
        if len(results) > 0:
            results = {}
        self.__populate_target_data(target, results)
        return results

    def get_instance_model(self):
        ins_data = {}
        for clas in self.model_map.keys():
            logging.debug("class: {}".format(clas))
            clas_ins = self.class_ins_map[clas]
            ins_data[clas] = {}
            attr_val_map = {}
            for attribute in self.model_map[clas]:
                attr_val = []
                if len(clas_ins) > 1:  # list by default for multiple instances
                    for ci in clas_ins:
                        logging.debug("attribute: {}".format(attribute.name) + " - value: {}".format(
                            ci.eGet(attribute.name)))
                        attr_val.append(ci.eGet(attribute.name))
                    attr_val_map[attribute.name] = attr_val
                    ins_data[clas] = attr_val_map
                else:
                    logging.debug("attribute: {}".format(attribute.name) + " - value: {}".format(
                        clas_ins[0].eGet(attribute.name)))
                    attr_val_map[attribute.name] = clas_ins[0].eGet(attribute.name)
                    ins_data[clas] = attr_val_map

        return ins_data

    # inner class
    class DTBehavior(threading.Thread):
        global model_root
        APD = DynamicEPackage(model_root)

        def __init__(self, ins_name, root_clas, clas_ins_map, clas_ref_map, model_map, apd_sm, sm_snippets):
            threading.Thread.__init__(self)
            self.daemon = True
            self.ins_name = ins_name
            self.root_clas = root_clas
            self.clas_ins_map = clas_ins_map
            self.clas_ref_map = clas_ref_map
            self.model_map = model_map

            # load SM metamodel
            res_set = ResourceSet()
            uri = URI('models/MiniFsm.ecore')
            package_root = res_set.get_resource(uri).contents[0]
            res_set.metamodel_registry[package_root.nsURI] = package_root
            # load APD-SM model
            uri = URI(apd_sm)
            resource = res_set.get_resource(uri)
            root = resource.contents[0]
            for rc in root.eContents:
                if 'pyecore.ecore.Transition' in str(type(rc)):
                    logging.debug("Transition: event - {}".format(rc.event)+" - incoming - {}".format(rc.incoming.name)+" - outgoing - {}".format(rc.outgoing.name))
                elif 'pyecore.ecore.State' in str(type(rc)):
                    logging.debug("State: {}".format(rc.name))
                else:
                    logging.debug("Start/Terminal: {}".format(rc))

            SnippetsLoader.load_sm_snippets(sm_snippets)

        def run(self):
            logging.info(
                "[APD-DT] Running DT behavior for '{}'".format(self.root_clas) + " - related instance: {}".format(
                    self.ins_name))
            clas_ins = self.clas_ins_map[self.root_clas]
            logging.debug("[APD-DT] self.clas_ref_map '{}'".format(self.clas_ref_map))
            clas_ins[0].start_up(self.clas_ins_map, self.clas_ref_map, self.model_map)

        @APD.Device.behavior
        def dispense_medicine(self, doses, date_time):
            logging.info("[APD-DT] Dispensing: doses = {}".format(doses) + " - for {}".format(date_time))
            time.sleep(5)
            input("[APD-DT] Press any key to indicate medication is taken")
            time.sleep(1)
            logging.info("[APD-DT] Dispensing finished")

        @APD.Device.behavior
        def check_schedule_updated(self):
            logging.info("[APD-DT] Checking if schedule is updated...")
            while True:
                # await asyncio.sleep(0.1)
                time.sleep(0.1)
                global is_updated
                if is_updated:
                    break

        @APD.Device.behavior
        def dispensing(self, med_schedule):
            logging.info('[APD-DT] Dispensing state...')
            logging.info("Medication schedule:: \n {}".format(med_schedule))
            scheduler = AsyncIOScheduler(timezone=datetime.datetime.utcnow().astimezone().tzinfo)
            date_times = []
            for med in med_schedule:
                med_detail = med.split(" ")
                date_time = med_detail[0] + " " + med_detail[1]
                date_times.append(date_time)
                doses = med_detail[2]
                # this is async job
                scheduler.add_job(self.dispense_medicine, 'date', run_date=date_time, args=[doses, date_time])

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            thread = Thread(target=loop.run_forever)
            thread.start()
            scheduler.start()
            while True:
                time.sleep(1)
                now = str(datetime.datetime.now())
                if now > max(date_times):
                    loop.call_soon_threadsafe(loop.stop)
                    break
            thread.join()
            logging.info('[APD-DT] Schedule is completed!...')

        @APD.Device.behavior
        def loading_schedule(self, clas_ins_map, clas_ref_map, model_map):
            first_time = True
            global is_updated
            while True:
                if first_time:
                    thread = Thread(target=self.check_schedule_updated, daemon=True)
                    thread.start()

                if is_updated or first_time:
                    first_time = False
                    is_updated = False
                    logging.info('[APD-DT] Loading schedule...')
                    plan_classes = []
                    for ck in clas_ref_map.keys():
                        if 'plan' in ck.lower():
                            plan_classes.append(ck)
                            plan_classes.append(clas_ref_map[ck][0])
                            for cr in clas_ref_map[ck]:
                                if cr in clas_ref_map.keys():
                                    plan_classes.append(clas_ref_map[cr][0])

                    counter = 0
                    multiple_plans = 0
                    med_plans = []
                    plan_keys = []
                    while True:  # can be any number of medication plans
                        plan_instances = []
                        plan_dict = {}
                        for plan_clas in plan_classes:
                            instances = clas_ins_map[plan_clas]
                            if len(instances) > 1:
                                multiple_plans = len(instances)
                                ins = instances[counter]
                                plan_instances.append(ins)
                                for attribute in model_map[plan_clas]:
                                    plan_dict[attribute.name] = ins.eGet(attribute.name)
                                    if 'date' in attribute.name or 'time' in attribute.name or 'day' in attribute.name or 'dose' in attribute.name:
                                        if attribute.name not in plan_keys:
                                            plan_keys.append(attribute.name)

                        # compile plans
                        med_plans.append(plan_dict)
                        if counter == multiple_plans - 1:
                            break
                        else:
                            counter += 1
                    med_schedule = []
                    for med_plan in med_plans:
                        first_dose_date = med_plan['first_dose_date']
                        period_days = int(med_plan['period_days'])
                        time = med_plan['time']
                        doses = med_plan['doses']

                        # check schedule is correct
                        if first_dose_date != datetime.datetime.today().date():
                            logging.info("[APD-DT] Incorrect first dose date! Using today's date [{}] instead.".format(
                                datetime.datetime.today().date()))
                            first_dose_date = datetime.datetime.today().date()
                        for _ in range(period_days):
                            daily_plan = str(first_dose_date) + " " + str(time) + " " + str(doses)
                            first_dose_date += datetime.timedelta(days=1)
                            med_schedule.append(daily_plan)

                    # if schedule is available
                    if len(med_schedule) > 0:
                        logging.info('[APD-DT] Medication schedule loaded...')
                        self.dispensing(med_schedule)
                    else:
                        logging.info('[APD-DT] No medication schedule! Waiting for the schedule...')

        @APD.Device.behavior
        @behavior.main
        def start_up(self, clas_ins_map, clas_ref_map, model_map):
            logging.info("[APD-DT] Starting device...")
            # auto transition to load schedule
            self.loading_schedule(clas_ins_map, clas_ref_map, model_map)


class ObserverThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.daemon = True
        self.is_updated = False

    def run(self):
        logging.debug("Running - {} - {}".format(threading.currentThread().getName(), self.is_updated))
        while True:
            global is_updated
            is_updated = self.queue.get()


class SnippetsLoader:
    @staticmethod
    def load_sm_snippets(sm_snippets):
        config = configparser.ConfigParser()
        config.read(sm_snippets)
        setup = config['APD-SM']['Setup']
        load_plan = config['APD-SM']['LoadMedicationPlan']
        check_plan = config['APD-SM']['CheckMedicationPlan']
        dispense = config['APD-SM']['Dispense']
        return setup, load_plan, check_plan, dispense

"""
Created on March 15, 2023

@author: Hassan Sartaj
@version: 1.0
"""

import configparser


dtserver_host = None
dtserver_port = None
ptserver_host = None
ptserver_port = None


class ConfigLoader:
    @staticmethod
    def load_configs(file='inputs/config.ini'):
        global dtserver_host, dtserver_port, ptserver_host, ptserver_port
        config = configparser.ConfigParser()
        config.read(file)
        dtserver_host = config['DTServer']['Host']
        dtserver_port = int(config['DTServer']['Port'])
        ptserver_host = config['PDServer']['Host']
        ptserver_port = int(config['PDServer']['Port'])

    @staticmethod
    def get_dtserver_host():
        global dtserver_host
        return dtserver_host

    @staticmethod
    def get_dtserver_port():
        global dtserver_port
        return dtserver_port

    @staticmethod
    def get_ptserver_host():
        global ptserver_host
        return ptserver_host

    @staticmethod
    def get_ptserver_port():
        global ptserver_port
        return ptserver_port

# read and sort config, initialize instruments, thermomenters and other objects
# HR@KIT/20019
#  
#import collections #.MutableMapping
from collections.abc import MutableMapping
import json
from threading import Lock
import configparser
from queue import SimpleQueue

from .tip_config_defaults import _config_defaults, _types_dict, _boolean, _int

# 
# thread save dictionary class
#
class SettingsDict(MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.store.update(dict(*args, **kwargs))  # use the free update to set keys
        self.settings_lock = Lock()

    def __getitem__(self, key):
        with self.settings_lock:
            return self.store[key]

    def __setitem__(self, key, value):
        with self.settings_lock:
            self.store[key] = value

    def __delitem__(self, key):
        with self.settings_lock:
            del self.store[key]

    def __iter__(self):
        with self.settings_lock:
            return iter(self.store)

    def __len__(self):
        with self.settings_lock:
            return len(self.store)

    def keys(self):
        with self.settings_lock:
            return self.store.keys()

    def items(self):
        with self.settings_lock:
            return self.store.items()

    def values(self):
        with self.settings_lock:
            return self.store.values()

    def update(self,the_dict):
        with self.settings_lock:
            self.store.update(the_dict) 

    def dump_json(self):
        with self.settings_lock:
            return json.dumps(self.store, indent = 2, sort_keys = True)
    
# 
# global config, thread save
# 

config  = SettingsDict()

#
# global device_instances, unused in the moment
# 

device_instances = SettingsDict()


#
# global internal states
# 

internal = SettingsDict()

#
# data log recorder queue (FIFO)
#

internal['dlr_queue'] = SimpleQueue()

#
# DLR datagram object to be posted vie the dlr_queue 
#
class dlr_datagram:
    device      = ""
    item        = ""
    value       = 0      # <- this is important, since the value, time  stored in the config can be outdated.
    change_time = 0      # <-



#
# map strings to their corresponding types
#
def convert_string_to_value(param, value):
        return _types_dict.get(param,str)(value)


def load_config(settings_file = "settings_local.cfg", debug = False):
    
    cp_conf = configparser.RawConfigParser(inline_comment_prefixes=';')
    # windows acts weird on open files...
    with open(settings_file) as f:
        cp_conf.read_file(f)
    #if debug:
    #    pprint.pprint({section: dict(cp_conf[section]) for section in cp_conf.sections()})
    return cp_conf

def convert_to_dict(cp_conf): # config parser results
    """ converts  a config parser configuration to dict of dicts 
        would probably be faster if we would use dictionaries instead of lists.
    """
    if 'system' in cp_conf.sections():
        version = cp_conf['system'].getfloat("settings_version",0)
        if version < 2.0:
            print ("ERROR: No settings version specified or settings file outdated: EXIT")
            raise Exception
    else:
        print ("ERROR: No 'system' specified or settings file outdated: EXIT")
        raise Exception

    
    for inst in cp_conf.sections():
        params = {}
        for param in cp_conf[inst].keys():
            if _types_dict.get(param,str) == _boolean:
                params[param] = cp_conf[inst].getboolean(param,False)
            if _types_dict.get(param,str) == _int:
                params[param] = cp_conf[inst].getint(param,-1)
            if _types_dict.get(param,str) == float:
                params[param] = cp_conf[inst].getfloat(param,-1.0)
            if _types_dict.get(param,str) == str:
                params[param] = cp_conf[inst].get(param,"")
        #
        # load the defaults first 
        # from _config_defaults 
        config[inst] = _config_defaults[params['type']].copy()
        # then update the central dict with the values from the settings file
        config[inst].update(params)

    # add an system internal area with a few defaults
    if config['system']:
        config['system']['abort'] = False
    else:
        config['system'] = {
                'version': 1.5,
                'abort': False,
        }
    
    return config


def update_active_devices(config):
    #
    #  some housekeeping lists for devices/instruments
    # 
    config['system']['defined_instruments'] = []
    config['system']['defined_thermometers'] = []
    config['system']['defined_generic_devices'] = []
    config['system']['defined_levelmeter_devices'] = []
    config['system']['defined_logger_facilities'] = []

    config['system']['active_devices'] = []
    config['system']['active_instruments'] = []
    config['system']['active_thermometers'] = []
    config['system']['active_generic_devices'] = []
    config['system']['active_levelmeter_devices'] = []
    config['system']['active_logger_facilities'] = []
 

    DI  = config['system']['defined_instruments']
    DT  = config['system']['defined_thermometers']
    DGD = config['system']['defined_generic_devices']
    DLD = config['system']['defined_levelmeter_devices']
    DLF = config['system']['defined_logger_facilities']

    AD  = config['system']['active_devices']
    AI  = config['system']['active_instruments']
    AT  = config['system']['active_thermometers']
    AGD = config['system']['active_generic_devices']
    ALD = config['system']['active_levelmeter_devices']
    ALF = config['system']['active_logger_facilities']

    for inst in config.keys():
        if config[inst].get("type","") == "instrument":
            DI.append(inst)
            if config[inst].get("active",False):
                AI.append(inst)
        if config[inst].get("type",False) == "thermometer":
            DT.append(inst)
            if config[inst].get("active",False):
                AT.append(inst)
                AD.append(inst)
        if config[inst].get("type",False) == "levelmeter":
            DLD.append(inst)
            if config[inst].get("active",False):
                ALD.append(inst)
                AD.append(inst)                
        if config[inst].get("type",False) in ["generic","hygrometer","scale"]:
            DGD.append(inst)
            if config[inst].get("active",False):
                AGD.append(inst)
                AD.append(inst)
        if config[inst].get("type",False) == "logger":
            DLF.append(inst)
            if config[inst].get("active",False):
                ALF.append(inst)
                AD.append(inst)






if __name__ == "__main__":

    config = convert_to_dict(load_config(settings_file="settings_local.cfg"))
    update_active_devices(config)
    #print (dump_json(config)
    print (json.dumps(config.store,indent=2,sort_keys=True))
# read and sort config, initialize instruments, thermomenters and other objects
# HR@KIT/20019
#  
import collections
import json
from threading import Lock
import configparser



# 
# thread save dictionary class
#
class SettingsDict(collections.MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys
        self.setings_lock = Lock()

    def __getitem__(self, key):
        with self.setings_lock:
            return self.store[key]

    def __setitem__(self, key, value):
        with self.setings_lock:
            self.store[key] = value

    def __delitem__(self, key):
        with self.setings_lock:
            del self.store[key]

    def __iter__(self):
        with self.setings_lock:
            return iter(self.store)

    def __len__(self):
        with self.setings_lock:
            return len(self.store)

    def keys(self):
        with self.setings_lock:
            return self.store.keys()

    def items(self):
        with self.setings_lock:
            return self.store.items()

    def values(self):
        with self.setings_lock:
            return self.store.values()

    def dump_json(self):
        with config.setings_lock:
            return json.dumps(self.store,indent=2,sort_keys=True)
    
# 
# global config, thread save
# 

config  = SettingsDict()

#
# global device_instances
# 

device_instances = SettingsDict()

#
# helper functons to convert string values into something useful
#
def _boolean(s): return s.lower() in ("yes", "true", "t", "1")
def _int(s): return int(float(s))

#
# mapping of parameter types
# 
_types_dict = { 'active':_boolean,'control_active':_boolean,'abort':_boolean,
                'port':_int, 'device_channel':_int, 'device_range':_int, 'device_excitation':_int,
                'control_channel':_int,
                'interval':float, 'device_integration_time':float, 'delay':float,
                'control_resistor':float, 'control_default_heat':float,
                'control_p':float, 'control_i':float, 'control_d':float,
                'version':float,
                'type':str, 'device':str, 'description':str, 'com_method':str, 'ip':str, 'url':str,
                'control_device':str,
                'calibration_file':str, 'calibration_description':str, 'calibration_interpolation':str,
                'calibration_file_order':str
            }


def load_config(settings_file = "settings_local.cfg", debug = False):
    # not used in the moment
    cp_conf = configparser.RawConfigParser(inline_comment_prefixes=';')
    cp_conf.read(settings_file)
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
            
        config[inst] = params
    # add an system internal area with a few defaults
    config['system'] = {
            'version': 1.5,
            'abort': False,
    }
    return config


def convert_string_to_value(param, value):
        return _types_dict.get(param,str)(value)

def update_active_devices(config):
    #
    #  some housekeeping lists for devices
    # 
    config['system']['defined_instruments'] = []
    config['system']['defined_thermometers'] = []
    config['system']['active_instruments'] = []
    config['system']['active_thermometers'] = []
    DI = config['system']['defined_instruments']
    DT = config['system']['defined_thermometers']
    AI = config['system']['active_instruments']
    AT = config['system']['active_thermometers']

    for inst in config.keys():
        if config[inst].get("type","") == "bridge":
            DI.append(inst)
            if config[inst].get("active",False):
                AI.append(inst)
        if config[inst].get("type","") == "heater":
            DI.append(inst)
            if config[inst].get("active",False):
                AI.append(inst)
        if config[inst].get("type",False) == "thermometer":
            DT.append(inst)
            if config[inst].get("active",False):
                AT.append(inst)






if __name__ == "__main__":

    config = convert_to_dict(load_config(settings_file="settings.cfg"))
    update_active_devices(config)
    #print (dump_json(config)
    print (json.dumps(config.store,indent=2,sort_keys=True))
# read and sort config, initialize instruments, thermomenters and other objects
# HR@KIT/20019
#  
from lib.tip_data import DATA
import configparser
import json
import pprint

#
# helper functons to convert string values into something useful
#
def _boolean(s): return s.lower() in ("yes", "true", "t", "1")
def _int(s): return int(float(s))

#
# mapping of parameter types
# 
types_dict = {  'active':_boolean,'control_active':_boolean,'abort':_boolean,
                'port':_int, 'device_channel':_int, 'device_range':_int, 'device_excitation':_int,
                'control_channel':_int,
                'scan_interval':float, 'device_integration_time':float, 'delay':float,
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
    if debug:
        pprint.pprint({section: dict(cp_conf[section]) for section in cp_conf.sections()})
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

    config = {}
    for inst in cp_conf.sections():
        #print(inst)
        params = {}
        for param in cp_conf[inst].keys():
            if types_dict.get(param,str) == _boolean:
                params[param] = cp_conf[inst].getboolean(param,False)
            if types_dict.get(param,str) == _int:
                params[param] = cp_conf[inst].getint(param,-1)
            if types_dict.get(param,str) == float:
                params[param] = cp_conf[inst].getfloat(param,-1.0)
            if types_dict.get(param,str) == str:
                params[param] = cp_conf[inst].get(param,"")
            
        config[inst] = params
    # add an system internal area with a few defaults
    config['system'] = {
            'version': 1.5,
            'abort': False,
    }
    return config


def convert_string_to_value(param, value):
        return types_dict.get(param,str)(value)

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

def dump_json(config):
    return json.dumps(config,indent=4,sort_keys=True)

if __name__ == "__main__":

    config = convert_to_dict(load_config())
    DATA = DATA(config)
    update_active_devices(config)
    print (dump_json(config))
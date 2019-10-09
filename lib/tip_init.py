# tip initialisation 

import importlib
from lib.tip_config import config, device_instances, load_config, convert_to_dict, update_active_devices
from lib.tip_devices import device, backend, thermometer
import devices.DriverTemplate_Bridge

def load_instruments(config):
    # load instruments first, since some devices, e.g. a thermometer depend on it. 
    # 
    print("Found instruments:")
    print(config['system']['defined_instruments'])
    print("Active instruments:")
    print(config['system']['active_instruments'])
    for inst in config['system']['active_instruments']:
        print(inst)
        #obj = importlib.import_module(config[inst]['device'],package = 'devices')
        obj = importlib.import_module("devices."+config[inst]['device'])
        #device_instances[inst] = backend(inst)



def load_thermometers(config):
    print("Found thermometers:")
    print(config['system']['defined_thermometers'])
    print("Active thermometers:")
    print(config['system']['active_thermometers'])

    for therm in config['system']['active_thermometers']:
        device_instances[therm] = thermometer(therm)
    
def tip_init (settings_file = "settings_local.cfg"):
    
    config = convert_to_dict(load_config(settings_file))

    update_active_devices(config)

    load_instruments(config)
    
    #load_thermometers(config)

    #print(config.dump_json())
    print(device_instances.items())

if __name__ == "__main__":

    tip_init()

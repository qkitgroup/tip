# tip initialisation 

import importlib
from lib.tip_config import config, device_instances, load_config, convert_to_dict, update_active_devices
from lib.tip_devices import device, thermometer
import devices.DriverTemplate_Bridge
from lib.tip_scheduler import tip_scheduler

def load_instruments(config):
    # load instruments first, since some devices, e.g. a thermometer depend on it. 
    # 
    print("Config: Found defined instruments: "+str(config['system']['defined_instruments']))
    print("Config: Active instruments: "+str(config['system']['active_instruments']))
    
    for inst in config['system']['active_instruments']:
        print("loading driver for: "+inst)
        #obj = importlib.import_module(config[inst]['device'],package = 'devices')
        backend = importlib.import_module("devices."+config[inst]['device'])
        device_instances[inst] = backend.driver(inst)

def load_thermometers(config):
    tip_sched  = tip_scheduler()
    
    print("Found thermometers: "+str(config['system']['defined_thermometers']))
    print("Active thermometers: "+str(config['system']['active_thermometers']))
    
    for therm in config['system']['active_thermometers']:
        device_instances[therm] = thermometer(therm)
        device_instances[therm].backend = device_instances[config[therm]["device"]]
        if config[therm]["control_device"]:
            device_instances[therm].control_device = device_instances[config[therm]["control_device"]]
        
        tip_sched.add_thermometer(device_instances[therm])

    tip_sched.run()

    
def tip_init (settings_file = "settings_local.cfg"):
    
    config = convert_to_dict(load_config(settings_file))

    update_active_devices(config)

    load_instruments(config)
    
    load_thermometers(config)

    #print(config.dump_json())
    print(device_instances.items())

if __name__ == "__main__":

    tip_init()

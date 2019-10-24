# tip initialisation 
import os
import logging
from time import strftime
import importlib
import tip
from lib.tip_config import config, device_instances, load_config, convert_to_dict, update_active_devices
from lib.tip_devices import device, thermometer
from lib.tip_scheduler import tip_scheduler
from lib.tip_zmq_server import srv_thread 

import devices.DriverTemplate_Bridge

def setup_logging():
    # everything is relative to the tip directory in the  moment: note the access rights
    tip_root_dir = os.path.split(tip.__file__)[0]
    format_str = "%(asctime)s %(levelname)-8s: %(message)s (%(filename)s:%(lineno)d)"
    logging.basicConfig(
        filename=os.path.join(tip_root_dir,config['system'].get('logdir','logs'), 
                                    strftime('tip_%Y%m%d_%H%M%S.log')),
        format=format_str,
        datefmt='%Y-%m-%d %H:%M:%S', 
        level=logging.INFO,
        filemode='a+'
        )
    

    fileLogger = logging.getLogger()
    formatter = logging.Formatter(format_str)
    logging.info(' ---------- LOGGING STARTED ---------- ')

    consoleLogger = logging.StreamHandler()
    consoleLogger.setFormatter(formatter)
    fileLogger.addHandler(consoleLogger)

    fileLogger.setLevel(logging.INFO)
    consoleLogger.setLevel(logging.DEBUG)

def load_instruments(config):
    # load instruments first, since some devices, e.g. a thermometer depend on it. 
    # 
    logging.info("Config: Found defined instruments: "+str(config['system']['defined_instruments']))
    logging.info("Config: Active instruments: "+str(config['system']['active_instruments']))
    
    for inst in config['system']['active_instruments']:
        logging.info("loading driver for: "+inst)
        #obj = importlib.import_module(config[inst]['device'],package = 'devices')
        backend = importlib.import_module("devices."+config[inst]['device'])
        device_instances[inst] = backend.driver(inst)

def load_thermometers(config):
    tip_sched  = tip_scheduler()
    
    logging.info("Found thermometers: "+str(config['system']['defined_thermometers']))
    logging.info("Active thermometers: "+str(config['system']['active_thermometers']))
    
    for therm in config['system']['active_thermometers']:
        device_instances[therm] = thermometer(therm)
        device_instances[therm].backend = device_instances[config[therm]["device"]]
        if config[therm]["control_device"]:
            device_instances[therm].control_device = device_instances[config[therm]["control_device"]]
        logging.info("add thermometer to scheduler: "+therm)
        tip_sched.add_thermometer(device_instances[therm])

    tip_sched.run()

    
def tip_init (settings_file = "settings_local.cfg"):
    
    config = convert_to_dict(load_config(settings_file))

    setup_logging()

    update_active_devices(config)

    srv_thread()

    load_instruments(config)
    
    load_thermometers(config)

    logging.info("Configuration at startup:"+config.dump_json())
    #print(device_instances.items())

if __name__ == "__main__":

    tip_init()

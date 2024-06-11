# tip initialisation 
import os
import logging
from time import strftime
import importlib
from queue import SimpleQueue
import tip
from lib.tip_config import config, internal, device_instances, load_config, convert_to_dict, update_active_devices
from lib.tip_devices import device, thermometer, levelmeter, generic_device
from lib.tip_scheduler import tip_scheduler
from lib.tip_zmq_server import srv_thread 
from lib.tip_data_log_recorder import data_log_recorder

import devices.DriverTemplate_Bridge

def setup_logging(config):
    # everything is relative to the tip directory in the  moment: note the access rights
    tip_root_dir = os.path.split(tip.__file__)[0]

    #set loglevel from config
    LLC = getattr(logging,config['system'].get("loglevel_console",'WARNING').upper())
    LLF = getattr(logging,config['system'].get("loglevel_file",'WARNING').upper())

    format_str = "%(asctime)s %(levelname)-8s: %(message)s (%(filename)s:%(lineno)d)"
    
    logging.basicConfig( 
        level=logging.DEBUG,
        format=format_str,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    formatter = logging.Formatter(format_str)
    
    log = logging.getLogger()
    FileLogger = logging.FileHandler(filename=os.path.join(tip_root_dir,config['system'].get('logdir','logs'), 
                                    strftime('tip_%Y%m%d_%H%M%S.log')),mode='a+')
    FileLogger.setFormatter(formatter)
    log.addHandler(FileLogger)

    logging.info(' ---------- LOGGING STARTED ---------- ')
    logging.info("loglevel console: "+ config['system'].get("loglevel_console",'WARNING'))
    logging.info("loglevel file: "+config['system'].get("loglevel_file",'WARNING'))

    FileLogger.setLevel(LLF)
    log.setLevel(LLC)




def load_instruments(config):
    # load instruments first, since some devices, e.g. thermometers, depend on it. 
    # 
    logging.info("Config: Found defined instruments: "+str(config['system']['defined_instruments']))
    logging.info("Config: Active instruments: "+str(config['system']['active_instruments']))
    
    for inst in config['system']['active_instruments']:
        logging.info("loading driver for: "+inst)
        # load the module
        backend = importlib.import_module("devices."+config[inst]['device'])
        device_instances[inst] = backend.driver(inst)

def load_thermometers(config,tip_sched):
    
    
    logging.info("Found thermometers: "+str(config['system']['defined_thermometers']))
    logging.info("Active thermometers: "+str(config['system']['active_thermometers']))
    
    for therm in config['system']['active_thermometers']:
        device_instances[therm] = thermometer(therm)
        device_instances[therm].backend = device_instances[config[therm]["device"]]
        if config[therm]["control_device"]: 
            # is the device active ?
            if config[config[therm]["control_device"]]['active']:
                device_instances[therm].control_device = device_instances[config[therm]["control_device"]]
        logging.info("add thermometer to scheduler: "+therm)
        tip_sched.add_thermometer(device_instances[therm])


def load_levelmeter_devices(config,tip_sched):
    
    
    logging.info("Found levelmeter device: " +str(config['system']['defined_levelmeter_devices']))
    logging.info("Active levelmeter device: "+str(config['system']['active_levelmeter_devices']))
    
    for device in config['system']['active_levelmeter_devices']:
        device_instances[device] = levelmeter(device)
        device_instances[device].backend = device_instances[config[device]["device"]]
        
        logging.info("add level device to scheduler: "+device)
        tip_sched.add_device(device_instances[device])
    



def load_generic_devices(config,tip_sched):
    
    
    logging.info("Found generic devices: "+str(config['system']['defined_generic_devices']))
    logging.info("Active generic devices: "+str(config['system']['active_generic_devices']))
    
    for device in config['system']['active_generic_devices']:
        device_instances[device] = generic_device(device)
        device_instances[device].backend = device_instances[config[device]["device"]]
        """
        if config[device]["control_device"]: 
            # is the device active ?
            if config[config[device]["control_device"]]['active']:
                device_instances[device].control_device = device_instances[config[device]["control_device"]]
        """
        logging.info("add generic device to scheduler: "+device)
        tip_sched.add_device(device_instances[device])


def setup_data_log_recorder(config,tip_sched):
    # data log recorder (dlr)
    # 
    logging.info("Start DATA LOG RECORDER (DLR) facility.")
    logging.info("Found logger facilities: " +str(config['system']['defined_logger_facilities']))
    logging.info("Active logger facilities: "+str(config['system']['active_logger_facilities']))
    
    for device in config['system']['active_logger_facilities']:
        logging.info(f"add logger device queue for: {device}")
        internal['dlr_queues'][device] = SimpleQueue()
        internal['dlr_submit_queues'][device] = list()

        device_instances[device] = data_log_recorder(device)
        #device_instances[device].backend = device_instances[config[device]["device"]] # influxdb ?!
        
        logging.info(f"add logger device to scheduler: {device}")
        tip_sched.add_device(device_instances[device])
    

    

    
def tip_init (settings_file = "settings_local.cfg"):
    
    config = convert_to_dict(load_config(settings_file))

    setup_logging(config)

    update_active_devices(config)

    srv_thread()

    load_instruments(config)
    
    tip_sched  = tip_scheduler()

    load_thermometers(config,tip_sched)
    
    load_levelmeter_devices(config,tip_sched)

    load_generic_devices(config,tip_sched)

    setup_data_log_recorder(config,tip_sched)

    tip_sched.run()
    #logging.info("Configuration at startup:"+config.dump_json())
    #print(device_instances.items())

if __name__ == "__main__":

    tip_init()

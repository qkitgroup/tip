# This file holds the definitions for the objets which are hooked into the TIP scheduler
# The objets should be derived from a base "device" class and add specific extensions, e.g. for a
# thermomenter, data loging, etc.
# written for TIP 2.0 by HR@KIT 2019 
from math import log10
import logging
from lib.tip_config import config, device_instances, _types_dict
from lib.tip_eich import TIPEich
from lib.tip_pidcontrol import pidcontrol

class device(object):

    def __init__(self,name):
        self.name  = name 
        self.backend = 0 # Backend is the device backend, e.g. a resistance bridge
        self.control_device = 0
        self.schedule_priority = 1
        #self._execute_func = self._hollow_func
        self.scheduler = None
        #self.abort = False

    def _hollow_func(self):
        # dummy 
        print ("dummy func executed ...")
        #time.sleep(2)
        return

    def schedule(self):
        """
        This function is called recursively with schedule_periode delays 
        from the scheduler. The scheduler is called after execute_func has been executed again, 
        which means that the total preiode is schedule_periode+duration_of(execute_func).
        """
        logging.debug("\nexec schedule() for " + self.name)
        logging.debug(self.name +" "+str(config[self.name]['interval']))


        if not config[self.name]['active']: return
        self._execute_func()
        # if abort is changed while _execute_func() is running, it would need another cycle, thus: 
        if not config[self.name]['active']: return  
        # recursive hook into the scheduler queue:
        self.scheduler.enter(config[self.name]['interval'], 
            self.schedule_priority, 
            self.schedule)

# class backend(device):
#     def __init__(self,name):
#         super(backend, self).__init__(name)
#         config[name]['last_error'] = ""
#         _types_dict['last_error'] = str

#     def _execute_func():
#         print("func <- executed!")
#         print(self.name)
        

class thermometer(device):
    def __init__(self,name):
        super(thermometer, self).__init__(name)
        logging.info("init thermometer:"+ name)
        #
        # update the configuration with temperature specific items
        # 
        config[name]['temperature'] = 0
        config[name]['control_temperature'] = 0
        config[name]['resistance'] = 0
        config[name]['heating_power'] = 0
        config[name]['heating_voltage'] = 0
        config[name]['heating_current'] = 0
        config[name]['sys_error'] = ""

        #
        # make the item types known
        # 

        _types_dict['temperature'] = float
        _types_dict['control_temperature'] = float
        _types_dict['resistance'] = float
        _types_dict['heating_power'] = float
        _types_dict['heating_voltage'] = float
        _types_dict['heating_current'] = float
        _types_dict['sys_error'] = str

        #
        # create a calibration object for the thermomenter
        #
        if config[name]['calibration_active']:
            self.calibration = TIPEich(
                config[name]['calibration_description'],
                config[name]['calibration_file'],
                config[name]['calibration_file_order'],
                config[name]['calibration_interpolation'])

            self.cal_key_formats = {}
            self.cal_key_formats['R'] = lambda R: R
            self.cal_key_formats['log10R'] = log10

        #
        # create a pid controller for the thermomenter
        #

        self.control = pidcontrol(name)

        #
        # Fixme missing: backend(R-Bridge), heater
        #

 
    def _execute_func(self):
        " This function gets periodically called by the scheduler "

        logging.debug("_execute_func called for "+self.name)
        
        self.backend.set_channel(     config[self.name]['device_channel'])
        self.backend.set_excitation(  config[self.name]['device_excitation'])
        self.backend.set_integration( config[self.name]['device_integration_time'])
        
        R = self.backend.get_resistance()
        config[self.name]['resistance']  = R
        logging.info (self.name + "\t R: %.01f "% (R))

        if config[self.name]['calibration_active']:
            Cal_R = self.cal_key_formats[config[self.name]['calibration_key_format']](R)
            T = self.calibration.get_T_from_R(Cal_R)
            config[self.name]['temperature'] = T
            logging.info (self.name + "\t T: %.05f "% (T))

            if config[self.name]['control_active']:
                new_heat_value = self.control.get_new_heat_value(T)
                
                logging.debug(self.control_device.get_idn())
                self.control_device.set_heater_channel(config[self.name]['control_channel'])
                self.control_device.set_heater_power(new_heat_value)
                
                config[self.name]['heating_power'] = new_heat_value



# This file holds the definitions for the objets which are hooked into the TIP scheduler
# The objets should be derived from a base "device" class and add specific extensions, e.g. for a
# thermomenter, data loging, etc.
# written for TIP 2.0 by HR@KIT 2019 
from math import log10
import time
import logging
from lib.tip_config import config, device_instances, internal ,dlr_datagram, _types_dict, _boolean, _int 
from lib.tip_eich import TIPEich
from lib.tip_pidcontrol import pidcontrol
# future adds:
#from lib.tip_carbon_copier import check_logfile, prepare_data, update_hdf_file

class device(object):

    def __init__(self,name):
        self.name  = name 
        self.backend = 0 # Backend is the device backend, e.g. a resistance bridge
        self.control_device = 0
        self.schedule_priority = 1
        #self._execute_func = self._hollow_func
        self.scheduler = None
        #self.abort = False
        config[name]['change_time'] = 0

    def _hollow_func(self):
        # dummy 
        print ("dummy func executed ...")
        #time.sleep(2)
        return

    def schedule(self):
        """
        This function is called recursively with schedule_periode delays 
        from the scheduler. The scheduler is called after execute_func has been executed again, 
        which means that the total periode is schedule_periode+duration_of(execute_func).
        """
        logging.debug("exec schedule() for " + self.name)
        logging.debug(self.name +" "+str(config[self.name]['interval']))


        if not config[self.name]['active']: return

        # this function does the heavy lifting 
        self._execute_func()

        # if abort is changed while _execute_func() is running, it would need another cycle, thus: 
        if not config[self.name]['active']: return  

        # recursive hook into the scheduler queue:
        self.scheduler.enter(config[self.name]['interval'], 
            self.schedule_priority, 
            self.schedule)
    
    def gather(self, mproperty, value, time):
        #
        # this is used to aggregate values to a list and save it in the central dict
        #

        # to limit space only gather values if wanted
        if not config[self.name]['gather']: return

        # variable to the config for the list of values: append a plural 's' ;)
        mproperties = mproperty + 's'

        # start with the previous list, or with a new one
        gathered_values = config[self.name].get(mproperties,[])
        change_times = config[self.name].get('change_times',[])


        # limit the number of entries to 'gather_max'
        if len(gathered_values) > config[self.name]['gather_max']:
            gathered_values.pop(0)
            change_times.pop(0)

        gathered_values.append(value)
        change_times.append(time)

        config[self.name][mproperties]    = gathered_values
        config[self.name]['change_times'] = change_times
    
    def dlr_record(self, device="", item="", value=0, change_time=0):
        #
        # data log recorder queue (e.g. with a influxdb backend)
        # this function appends a log item to a -thread independent-  global queue
        #
        if config['system']['active_logger_facilities']:
            #logging.debug(f"active logger facilities {config['system']['active_logger_facilities']}")
            logging.debug(f"DLR-record dev:{device} it:{item} val:{value} ct:{change_time}")
            dlr_dg = dlr_datagram()

            dlr_dg.device      = device
            dlr_dg.item        = item
            dlr_dg.value       = value
            dlr_dg.change_time = change_time

            internal['dlr_queue'].put(dlr_dg)


# the thermometer class is thermometer specific, probably one of the few places in the entire code. 
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

        logging.debug("_execute_func called for " + self.name)
        
        self.backend.set_channel(     config[self.name]['device_channel'])
        self.backend.set_excitation(  config[self.name]['device_excitation'])
        self.backend.set_integration( config[self.name]['device_integration_time'])

        m_property = config[self.name].get('property','resistance').lower()

        if  m_property == 'resistance':
            R = self.backend.get_resistance()
            if R == 0:
                logging.warning(self.name + "\t Bridge reported zero resistance. Retry...")
                R = self.backend.get_resistance()
                if R == 0:
                    logging.warning(self.name + "\t Bridge reported zero resistance. Skipping.")
                    return None

            config[self.name]['resistance']  = R
            logging.info (self.name + "\t R: %.05f Ohm"% (R))

            #
            # update the timestamp
            #
            config[self.name]['change_time'] = time.time()
            
            #
            # log the value to the data log recorder
            #
            self.dlr_record(
                device       = self.name,
                item         = 'resistance',
                value        = config[self.name]['resistance'],
                change_time  = config[self.name]['change_time']
                )

        elif m_property == 'temperature':
            T = self.backend.get_temperature()
            config[self.name]['temperature']  = T
            logging.info (self.name + "\t T: %.01f "% (T))

            #
            # update the timestamp
            #
            config[self.name]['change_time'] = time.time()

            #
            # log the value to the data log recorder
            #
            self.dlr_record(
                device       = self.name,
                item         = 'temperature',
                value        = config[self.name]['temperature'],
                change_time  = config[self.name]['change_time']
                )

        if config[self.name]['calibration_active']:
            Cal_R = self.cal_key_formats[config[self.name]['calibration_key_format']](R)
            T = self.calibration.get_T_from_R(Cal_R)
            config[self.name]['temperature'] = T
            logging.info (self.name + "\t T: %.05f K"% (T))

            #
            # log the value to the data log recorder
            #
            self.dlr_record(
                device       = self.name,
                item         = 'temperature',
                value        = config[self.name]['temperature'],
                change_time  = config[self.name]['change_time']
                )

            

            if config[self.name]['control_active'] and config[config[self.name]['control_device']]['active']:
                logging.debug('[^]<- entered control part')
                new_heat_value = self.control.get_new_heat_value(T)
                
                logging.debug(self.control_device.get_idn())
                self.control_device.set_heater_channel(config[self.name]['control_channel'])
                self.control_device.set_heater_power(new_heat_value)
                
                config[self.name]['heating_power'] = new_heat_value
                logging.info('%s Heat: %.02f uW'%(self.name, new_heat_value*1e6))

                #
                # log the value to the data log recorder
                #
                self.dlr_record(
                    device       = self.name,
                    item         = 'heating_power',
                    value        = config[self.name]['heating_power'],
                    change_time  = config[self.name]['change_time']
                    )
                logging.debug('[^]-> leave control part')
    # end of thermometer class

# scale_device. 
class levelmeter(device):
    def __init__(self,name):
        super(levelmeter, self).__init__(name)
        logging.info("init levelmeter device:"+ name)
        self.measure_property = config[name]['property']
        #
        # update the configuration with 'property' specific items
        # 
        config[name][self.measure_property] = 0
        config[name]['relative_level'] = 0
        config[name]['sys_error'] = ""
        #
        # make the item types known
        # 
        _types_dict[self.measure_property] = float
        _types_dict['sys_error'] = str

    def _execute_func(self):
        " This function gets periodically called by the scheduler "

        logging.debug("_execute_func called for "+self.name)
        
        self.backend.set_channel(     config[self.name]['device_channel'])
        self.backend.set_excitation(  config[self.name]['device_excitation'])
        self.backend.set_integration( config[self.name]['device_integration_time'])
        
        value = getattr(self.backend,"get_"+self.measure_property)()

        config[self.name][self.measure_property]  = value

        #
        # compute the relative N2 fill
        # 
        fl = config[self.name]['full_level']

        if fl == 0: 
            fl = 1 # prevent division by zero
            logging.error("full_level has to be >0")

        zl = config[self.name]['zero_level']
        rl = (value-zl)/(fl-zl)
        config[self.name]['relative_level'] = rl
        logging.info (self.name + "\t %s: %.01f "% (self.measure_property,value))
        logging.info (self.name + "\t %s: %.02f "% ("relative_level",rl))

        #
        # update the modification timestamp
        #
        config[self.name]['change_time'] = time.time()



# misc_device. 
class generic_device(device):
    """
    A generic device needs no 'special' general treatment, however, 
    possible more code in the driver
    """
    def __init__(self,name):
        super(generic_device, self).__init__(name)
        logging.info("init generic device:"+ name)

        self.measure_property = config[name]['property']
        #
        # update the configuration with 'property' specific items
        # 
        

        config[name][self.measure_property] = 0
        config[name]['sys_error'] = ""

        #
        # make the item types known
        # 
        
        _types_dict[self.measure_property] = float
        _types_dict['sys_error'] = str



    def _execute_func(self):
        " This function gets periodically called by the scheduler "

        logging.debug("_execute_func called for "+self.name)
        
        self.backend.set_channel(     config[self.name]['device_channel'])
        #self.backend.set_excitation(  config[self.name]['device_excitation'])
        #self.backend.set_integration( config[self.name]['device_integration_time'])

        #    
        # get the [measurement] value from the instrument   
        #
        if config[self.name]['has_timestamp']:
            value, timestamp = getattr(self.backend,"get_"+self.measure_property)()
            config[self.name][self.measure_property]  = value

            #
            # update the modification timestamp
            #
            config[self.name]['change_time'] = timestamp

        else:
            value = getattr(self.backend,"get_"+self.measure_property)()
            config[self.name][self.measure_property]  = value

            #
            # update the modification timestamp
            #
            timestamp = time.time()
            config[self.name]['change_time'] = timestamp
        
        #
        # log the value to the data log recorder
        #
        if config[self.name][self.measure_property] is not None:
            self.dlr_record(
                device       = self.name,
                item         = self.measure_property,
                value        = config[self.name][self.measure_property],
                change_time  = config[self.name]['change_time']
                )
        #
        # update the list of values, if configured
        # updates the config at 
        # 'measure_property'+'s'
        # 'change_times'
        self.gather(self.measure_property, value, timestamp)

        # tell what happened
        #logging.info (self.name + "\t %s: %.01f "% (self.measure_property,value))
        if value is not None:
            logging.info (f"{self.name}\t{self.measure_property}: {value:.03e} {config[self.name]['unit']} at {timestamp}")
        else:
            logging.info (f"{self.name}\t{self.measure_property}: {value} {config[self.name]['unit']} at {timestamp}")
     

        
# This file holds the definitions for the objets which are hooked into the TIP scheduler
# The objets should be derived from a base "device" class and add specific extensions, e.g. for a
# thermomenter, data loging, etc.
# written for TIP 2.0 by HR@KIT 2019 

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
        print("\nexec schedule() for " + self.name)
        print(self.name +" "+str(config[self.name]['interval']))


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
        print("init thermometer:"+ name)
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

        self.calibration = TIPEich(
            config[name]['calibration_description'],
            config[name]['calibration_file'],
            config[name]['calibration_file_order'],
            config[name]['calibration_interpolation'])

        #
        # create a pid controller for the thermomenter
        #

        self.control = pidcontrol(name)

        #
        # Fixme missing: backend(R-Bridge), heater
        #

 
    def _execute_func(self):
        " This function gets periodically called by the scheduler "

        print("func <- executed!")
        print(self.name)
        
        self.backend.set_channel(     config[self.name]['device_channel'])
        self.backend.set_excitation(  config[self.name]['device_excitation'])
        self.backend.set_integration( config[self.name]['device_integration_time'])
        
        R = self.backend.get_resistance()
        T = self.calibration.getT_from_R(R)

        config[self.name]['resistance']  = R
        config[self.name]['temperature'] = T

        if config[self.name]['control_active']:
            new_heat_value = self.control.get_new_heat_value(T)
            
            print(self.control_device.get_idn())
            self.control_device.set_heater_channel(config[self.name]['control_channel'])
            self.control_device.set_heater_power(new_heat_value)
            
            config[self.name]['heating_power'] = new_heat_value


""" 
" Helper classes "
class resistance_bridge(object):
    "these parameters are set every time the bridge is called"
    return_type =  0  # {0:"resistance",1:"phase"}
    channel = 0
    resistance_range = 0
    measure_excitation = 0
    integration_time = 0

class temperature_calibration(object):
    " These parameters are called every time the TIPeich is called
        When the calibration_file_name is "" and the 
        interpolation type is "" the value is simply returned.
        This is useful when the resistance bridge is returning an 
        already calibrated temperature.
    "
    thermometer_name = ""
    # the calibration file is searched in the "calibrations" folder and nowhere else
    calibration_file_name = ""
    column_resistance_temperature_order = "LR"
    interpolaton_type = "linear"



        class TEMPERATURE(object):
			def __init__(self,config,chindex):
				self.channel = chindex
				self.range = config.getint('T_Channel_%i'%chindex,'range')
				self.excitation = config.getint('T_Channel_%i'%chindex,'excitation')
				self.scan_interval = config.getfloat('T_Channel_%i'%chindex,'scan_interval')
				self.settling_time = config.getfloat('T_Channel_%i'%chindex,'settling_time')
				self.Temp = numpy.zeros(100)
				self.timestamps = numpy.zeros(100)#*time()
				self.countdown = self.scan_interval-1
				self.last_Res = 0
				self.tainted = False
				self.next_schedule = time() + self.scan_interval

				self.CP = TE.TIPEich(
					config.get('T_Channel_%i'%chindex,'Name'),
					config.get('T_Channel_%i'%chindex,'FName'),
					config.get('T_Channel_%i'%chindex,'FOrder'),
					config.get('T_Channel_%i'%chindex,'Interpolation')
				)
				print ("Channel %i loaded"%self.channel)
			
			def set_Range(self,Range):
				with self.bridge_lock:
					self.tainted = True
					self.range = Range
					return(1)
			def get_Range(self):
				return self.range

			def set_Excitation(self,Excitation):
				with self.bridge_lock:
					self.tainted = True
					self.excitation = Excitation
					return(1)
			def get_Excitation(self):
				return self.excitation			
			
			def get_last_Temp(self):
				return self.Temp[-1]
			
			def get_Temp(self):
				return self.Temp
			
			def store_T(self,temperature):
				lock = Lock()
				with lock:
					if numpy.max(self.Temp) == 0:
						self.Temp[:] = temperature
						self.timestamps[:] = time()
					else:
						self.Temp = numpy.delete(numpy.append(self.Temp,temperature),0)
						self.timestamps = numpy.delete(numpy.append(self.timestamps,time()),0)

			def store_R(self,R,convert=False):
				self.last_Res = R
				if convert:
					self._convert(R)
			
			def _convert(self,R):
				self.store_T(self.CP.getT_from_R(R))
				
			def get_R(self):
				return self.last_Res
			
			def get_age(self):
				return time()-self.timestamps[-1]
			
			def get_timestamps(self):
				return self.timestamps
			
			def get_all(self):
				return {"thermometer" : self.channel,
						"name": cp.thermometer,
						"temperature": self.get_Temp(),
						"timestamps": self.get_timestamps(),
						"range":self.get_Range(),
						"excitation":self.get_Excitation(),
						"resistance":self.get_R(),
						}
			
			def schedule(self):
				if self.next_schedule < time():
					while(self.next_schedule < time()):
						self.next_schedule += self.scan_interval
					return True
				else:
					return False
				#return self.get_age() >= self.scan_interval
				# if self.countdown == 0:
					# self.countdown = self.scan_interval-1
					# return True
				# else:
					# self.countdown -= 1
					# return False


		def __init__(self,config):
			#self.Control_Channel = self.config.getint('T_Channels','Control_Channel')
			#self.channels = numpy.array(self.config.get('T_Channels','Channels').split(","),dtype=numpy.int)
			#self.range = {}
			#self.excitation = {}
			#self.scan_interval = {}
			#self.settling_time = {}
			self.bridge_lock = Lock()
			self.tainted = True
			self.channel = 0
			#self.channels = [self.TEMPERATURE(config,CH) for CH in numpy.array(config.get('T_Channels','Channels').split(","),dtype=numpy.int) ]
			self.channels = [self.TEMPERATURE(config,int(CH)) for CH in 
							config.get('T_Channels','Channels').split(",")]
			self.chmap = {self.channels[i].channel : i for i in range(len(self.channels))}
			self.Control_Channel = self.channels[numpy.where(numpy.array(
				config.get('T_Channels','Channels').split(","),dtype=numpy.int) == 
				config.getint('T_Channels','Control_Channel') )[0][0]]
	
		def get_channel(self):
			return self.channel
		def set_channel(self,channel):
			self.channel = channel
			return True


# tip resistance brige setup for TIP 2 
# in TIP1 tis was a class ... DRY
import atexit

def init_resistance_bridge(self,backend):
    print ("Open and setup Bridge, may take a couple of seconds...")
    # import bridge hardware class
    if backend == 'PW_AVS47':
        print ("Initializing AVS47 ...")
        BR = setup_device_AVS47()
        print ("Done.")
        return BR
    elif backend == 'SRS_SIM900':
        print ("Initializing SIM921 ...")
        BR = setup_device_SIM921()
        print ("Done.")
        return BR
    elif backend == 'Lakeshore_370':
        print ("Initializing Lakeshore 370...")
        BR = setup_device_LS370()
        print ("Done.")
        return BR
    elif self.config.get('RBridge','Name').strip() == 'DummyBridge':
        from devices.DummyDevice import DummyDevice
        BR = DummyDevice("DummMe")
        print ("Dummy bridge init")
        return BR
    else
        return None
    
    # make sure that we gracefully go down
    atexit.register(self.disconnect)
    
def setup_device_AVS47(self):
    import devices.Picowatt_AVS47 as AVS
    
    if self.config.get('RBridge','Com_Method').strip() == 'Ethernet':
        BR = AVS.Picowatt_AVS47(
            self.config.get('RBridge','Name'),
            'GPIB::'+self.config.get('RBridge','GPIB_Addr').strip(),
            ip=self.config.get('RBridge','IP'),
            delay=self.config.getfloat('RBridge','delay'),
        )
    # basic setup
    BR._open()
    BR._set_remote()
    # set avs bridge from zero to measure, if not already there
    BR._set_input(1)
    
    # channel, excitation, range : avs specific, so far
    BR._set_channel(self.config.getint('RBridge','default_channel'),
                            self.config.getint('RBridge','default_excitation'),
                            self.config.getint('RBridge','default_range')
                            )
    return BR
    
def setup_device_SIM921(self):
    import devices.SRS_SIM900 as SIM
    "def __init__(self,ip= ,gpib="GPIB::0",SIM921_port=6,SIM925_port=8):"
    if self.config.get('RBridge','Com_Method').strip() == 'Ethernet':
        BR = SIM.SIM900(
            self.config.get('RBridge','Name'),
            gpib='GPIB::'+self.config.get('RBridge','GPIB_Addr').strip(),
            ip=self.config.get('RBridge','IP'),
            delay=self.config.getfloat('RBridge','delay'),
            SIM921_port=self.config.getint('RBridge','SIM921_port'), #6 Bridge
            SIM925_port=self.config.getint('RBridge','SIM925_port'), #8 multiplexer
            SIM928_port=self.config.getint('RBridge','SIM928_port')         
            )
        return BR
    else:
        pass
    
    
def setup_device_LS370(self):
    import devices.Lakeshore_370 as LS370
    "def __init__(self,ip= ,gpib="GPIB::0"):"
    if self.config.get('RBridge','Com_Method').strip() == 'Ethernet':
        BR = LS370.Lakeshore_370(
            self.config.get('RBridge','Name'),
            gpib='GPIB::'+self.config.get('RBridge','GPIB_Addr').strip(),
            ip=self.config.get('RBridge','IP'),
            delay=self.config.getfloat('RBridge','delay')
            )
        print ('LS enabled')
        return BR
    else:
        print ('Lakeshore 370 not setup')
        

    

        
    def set_Channel(self,Channel): #Channel is a TEMPERATURE Object
        print ("-> %s:             waiting %.1fs"%(Channel.channel,Channel.settling_time))
        self.BR._set_Excitation(-1) #-1 is excitation off for SIM900
        self.BR._set_Channel(Channel.channel)
        self.BR._set_Range(Channel.range)
        self.BR._set_Excitation(Channel.excitation)
        return self.BR._get_Channel()==Channel.channel


    def disconnect(self):
            print ("disconnecting the bridge ...")
            self.BR._set_local()
            self.BR._close() 
"""
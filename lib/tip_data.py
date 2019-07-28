#!/usr/bin/env python
# TIP DATA class version 0.2 written by HR@KIT Dec 2011
# to do
# make the _whole_ thing thread safe.

import numpy
#import thread
from time import time
from threading import Lock, Thread
try:
	import cPickle as pickle
except:
	import pickle
import lib.tip_eich as TE

# DATA exchange class, also holds global variables for
# Thread management

class DATA(object):
	class remote_info(object):
		last_Temp=0
		last_pidE=0
		last_Heat=0
		last_Temps = []

	class LOCALHOST(object):
		def __init__(self,config):
			self.name = config.get('LOCALHOST','name')
			self.ip	  = config.get('LOCALHOST','ip')
			self.port = config.getint('LOCALHOST','port')
	class REMOTEHOST(object):
		def __init__(self,config):
			self.name = config.get('REMOTEHOST','name')
			self.ip	  = config.get('REMOTEHOST','ip')
			self.port = config.getint('REMOTEHOST','port')
	
	
	class BRIDGE(object):
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
			self.channels = [self.TEMPERATURE(config,int(CH)) for CH in config.get('T_Channels','Channels').split(",")]
			self.chmap = {self.channels[i].channel : i for i in range(len(self.channels))}
			self.Control_Channel = self.channels[numpy.where(numpy.array(config.get('T_Channels','Channels').split(","),dtype=numpy.int) == config.getint('T_Channels','Control_Channel') )[0][0]]
	
		def get_channel(self):
			return self.channel
		def set_channel(self,channel):
			self.channel = channel
			return True
			
			
	class HEATER(object):
		def __init__(self,config):
			self.Resistor = config.getfloat('Heater',"Resistor")

	def __init__(self,config):
		# tip variables
		self.Running = True
		self.wants_abort = False
		self.debug = True
		self.cycle_time = config.getfloat('tip','cycle_time')

		self.last_pidE=0
		self.last_Rate=0
		self.last_Heat=0
		self.last_Temp=0
		self.last_Res=0
		self.pidE = numpy.zeros(100)
		self.Heat = numpy.zeros(100)
		self.Temp = numpy.zeros(100)
		self.ctrl_PID = (0.05,0.01,0)
		self.ctrl_T = 0
		self.config = ""
 
		# subclasses
		self.bridge = self.BRIDGE(config)
		self.heater = self.HEATER(config)
		self.localhost	= self.LOCALHOST(config)
		self.remotehost = self.REMOTEHOST(config)
		# locks
		self.ctrl_lock = Lock()

	def get_wants_abort(self):
		return self.wants_abort
	def set_wants_abort(self):
		self.wants_abort = True

	def get_pidE(self):
		return self.pidE
	def get_Rate(self):
		return self.Rate
	def get_Heat(self):
		return self.Heat
	def get_Temp(self):
		return self.Temp
	def get_PID(self):
		return self.ctrl_PID
	def set_P(self,P):
		self.ctrl_PID[0] = P
	def set_I(self,I):
		self.ctrl_PID[1] = I
	def set_P(self,D):
		self.ctrl_PID[2] = D
	def set_PID(self,PID):
		self.ctrl_PID = PID

	def set_Heat(self,heat_volt):
		
		lock = Lock()
		with lock:
			heat=heat_volt*heat_volt/self.heater.Resistor
			self.last_Heat=heat
			self.Heat = numpy.delete(numpy.append(self.Heat,heat),0)
	def set_Temp(self,T):
		lock = Lock()
		with lock:
			if numpy.max(self.Temp) == 0:
				self.Temp[:] = T
			self.last_Temp=T
			self.Temp = numpy.delete(numpy.append(self.Temp,T),0)
	def set_ctrl_Temp(self,T):
		with self.ctrl_lock:
			self.ctrl_T = T
	def get_ctrl_Temp(self):
		return self.ctrl_T

	def set_pidE(self,error):
		lock = Lock()
		with lock:
			self.last_pidE = error
			self.pidE = numpy.delete(numpy.append(self.pidE,error),0)

	def get_last_pidE(self):
		return self.last_pidE
		
	def get_last_Heat(self):
		return self.last_Heat
	def get_last_Temp(self):
		return self.last_Temp
	def set_last_Res(self,Res):
		self.last_Res = Res
	def get_last_Res(self):
		return self.last_Res
	def get_remote_info(self):
		remote_lock = lock()
		with remote_lock:
			ri=remote_info()
			ri.last_temp = self.get_Temp()
			ri.last_pidE = self.get_pidE()
			ri.last_heat = self.get_Heat()
			return pickle.dumps(ri)
	def get_all_pid(self):
		return {
				"P":self.get_PID()[0],
				"I":self.get_PID()[1],
				"D":self.get_PID()[2],
				"heat":self.get_Heat(),
				"error":self.get_pidE(),
				"tctrl":self.get_ctrl_Temp(),
				}
		
		
class GUI_DATA(object):
	def __init__(self):
		# tip variables
		self.Running = True
		self.wants_abort = False
		self.debug = True
		self.cycle_time = 0.5
		

if __name__ == "__main__":
	DATA = DATA()

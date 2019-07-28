# TIP DEV version 0.2 written by HR@KIT 2010

import random
import time,sys
import atexit
import math

# devices
import lib.tip_R_Bridge as tip_R_Bridge

# package pyserial, available at pypi if not in the std. distribution
# import serial

from threading import Thread 
from threading import Lock
# two small classes for simple devs, not used in tip in the moment



class Heater_Dev(object):
	class dummyheater(object):
		def set_output0(self,value):
			pass
		def set_output1(self,value):
			pass

	def __init__(self,DATA):
		self.DATA =DATA
		self.Heater_R = DATA.heater.Resistor
		if DATA.config.getboolean('debug','dummymode'):
			self.HDev = self.dummyheater()
			
		elif DATA.config.get('Heater',"Output_device").strip() == "LabJack":
			try:
				import devices.LabJack as LabJack
				self.HDev = LabJack.LabJack()
			except:
				print("LabJack not found, using dummy heater.")
				self.HDev = self.dummyheater()
		elif DATA.config.get('Heater',"Output_device").strip() == "NI-DAQ":
			try:
				print('HEATER set to nidaq')
				import devices.nidaq4 as nidaq
				self.HDev = nidaq
			except:
				print("NI-DAQ not found, using dummy heater.")
				self.HDev = self.dummyheater()
		elif DATA.config.get('Heater',"Output_device").strip() == "SRS_SIM928":
			try:
				print ('HEATER set to SRS_SIM928')
				# we assume, SIM921 is our bridge
				if DATA.config.get('RBridge','Name').strip() == 'SRS_SIM900':
				   self.HDev = DATA.RBR
				   print ( "SIM928: setting output to zero:",self.HDev.set_output0(0))
				   print ("Switching on SIM928: ",self.HDev.set_output_ON())
				else:
				   raise "NOT SIM921/SIM928/SIM900"
			except:
				print("SIM928 not found, using dummy heater.")
				self.HDev = self.dummyheater()
		elif DATA.config.get('Heater',"Output_device").strip() == "Lakeshore_370":
			try:
				print ('HEATER set to Lakeshore 370')
				#import devices.nidaq4 as nidaq
				self.HDev = DATA.RBR
			except:
				print("Lakeshore 370 not found, using dummy heater.")
				self.HDev = self.dummyheater()
		else:
			pass


	def set_Heat(self,value):
		# the Lakeshore 370 has its own heater:
		if self.DATA.config.get('Heater',"Output_device").strip() == "Lakeshore_370":
			if value < 0 : value = 0
			self.HDev.set_Heat(value)
			return value
		
		else:
				# calculate Heat for Black Fridge (R=600Ohm)
			if value < 0 :
				value = 0
			OUT_Volt = math.sqrt(value*self.Heater_R)
			print ("Set Heat voltage to "+str(OUT_Volt))
			# sanity check
			if OUT_Volt > 1.999:
				OUT_Volt = 1.999
			OUT_Volt=OUT_Volt/10.
			self.HDev.set_output0(OUT_Volt)
			return OUT_Volt

	def set_Heat_High_res(self,value):
		self.HDev.set_output1(value)

class IO_worker(Thread):
	" start a thread and get/set the IO data"
	def __init__(self,DATA):
		self.DATA = DATA
		Thread.__init__(self) 
		#self.rate = Rate_Dev()
		#print self.DATA.config.get('RBridge', 'GPIB_Addr')
		#time.sleep(2)

		self.RBR = tip_R_Bridge.R_bridge(self.DATA)
		#
		# we save the bridge object reference in the DATA class for
		# later use, e.g. for the SIM928 Voltage source (heater)
		#print dir(self.RBR)
		self.DATA.RBR = self.RBR.BR
		self.HTR = Heater_Dev(self.DATA)
		
		#self.curr = Current_Dev()

	def run(self):
		#set initial values
		#BRange = self.DATA.bridge.get_Range()
		#BExcitation = self.DATA.bridge.get_Excitation()
		#BChannel = self.DATA.bridge.get_Channel()
		
		Regulating = (self.DATA.get_ctrl_Temp() != 0)
		
		while True:
			if not self.DATA.Running:
				return
			
			# check if the range changed, this is something like an ISR
			# but polled
			# if BRange != self.DATA.bridge.get_Range():
				# BRange = self.DATA.bridge.get_Range()
				# # set the new range, AVS47 waits 3 secs
				# NR = self.RBR.set_Range(BRange)
				# if NR!=BRange:
					# print "Range change failed"
			#print "we are now"+(" " if Regulating else " not ")+"regulating"		
			if Regulating:
				if self.DATA.bridge.Control_Channel.tainted:
					print ("Range or Excitation was changed remotely. Updating device....")
					self.RBR.set_Channel(self.DATA.bridge.Control_Channel)
					self.DATA.bridge.channel.tainted = False
					
				if self.DATA.config.get('RBridge','Name').strip() == 'Lakeshore_370':
					self.DATA.bridge.Control_Channel.store_T(self.RBR.get_T())
					self.DATA.bridge.Control_Channel.store_R(self.RBR.get_R(),convert=False)
				else:
					self.DATA.bridge.Control_Channel.store_R(self.RBR.get_R(),convert=True)
				
				T = self.DATA.bridge.Control_Channel.get_last_Temp()
				R = self.DATA.bridge.Control_Channel.get_R()
				if self.DATA.config.getboolean('Heater',"Thermostage"): #Catch if any [...] wants to blow out the mixture
					if T > 2.0:
						self.HTR.set_Heat(0)
						self.DATA.set_ctrl_Temp(0)
				else:
					if T > 0.8:
						self.HTR.set_Heat(0)
						self.DATA.set_ctrl_Temp(0)
				# update the PID controller
				NHW,error = self.DATA.PID.update_Heat(T)
				# set calculated new heat (NHW)
				HT=self.HTR.set_Heat(NHW)
				# save it in the data objects
				self.DATA.set_Heat(HT)				
				if self.DATA.debug:
					print ("T=%.2fmK R=%.2fOhm Heat %0.4f(V) %.4f(uW)" % (T*1000,R,HT,HT**2/480*1e6))
				self.DATA.set_pidE(error)

				if self.DATA.get_ctrl_Temp() == 0: #We are no longer regulating
					Regulating = False
					print ("Disabling PID control and continue monitoring...")
				
				
			else: #We are currently not regulating the temperature
				if self.DATA.get_ctrl_Temp() != 0: #Oops, now we ARE regulating... Some things have to be done once..
					Regulating = True
					print ("Enabling PID control...")
					BChannel = self.DATA.bridge.Control_Channel #Switch to control channel
					if not self.RBR.set_Channel(BChannel):
						raise "Channel change failed"
					else:
						print("Channel changed to "+str(BChannel.channel)+" to enable temperature control.")
					continue
				else: #Now we are really not regulating...
					if self.DATA.bridge.channel != self.RBR.get_Channel():
						print ("!! Channel was changed on Bridge manually! Waiting one minute...")
						for _ in range(20): #this is necessary as we can not escape time.sleep with Ctrl+C and our programme would be frozen for 60sec. Now it only sleeps for 3 secs which is reasonable.
							time.sleep(3) 
					for TCH in self.DATA.bridge.channels:
						if TCH.schedule():	
							
							if self.DATA.bridge.channel != TCH.channel or TCH.tainted:
								self.RBR.set_Channel(TCH)
								self.DATA.bridge.set_channel(TCH.channel)
								TCH.tainted = False
								time.sleep(TCH.settling_time)
								if self.DATA.bridge.channel != self.RBR.get_Channel():
									print ("!! Channel changed within settling time! I will notice this again in a second...")
									break
							if self.DATA.config.get('RBridge','Name').strip() == 'Lakeshore_370':
								TCH.store_T(self.RBR.get_T())
								TCH.store_R(self.RBR.get_R(),convert=False)
							else:
								TCH.store_R(self.RBR.get_R(),convert=True)
							if self.DATA.debug:
								print( "CH %i: "%TCH.channel+\
									("T = %6.4f mK <-> "%(TCH.get_last_Temp()*1000) if TCH.get_last_Temp()<.9 else "T = %6.4f K <-> "%TCH.get_last_Temp()) +\
									("R = %6.4f kOhm"%(TCH.get_R()/1000) if TCH.get_R()>1500 else "R = %6.4f Ohm"%TCH.get_R() ))
			time.sleep(self.DATA.cycle_time)



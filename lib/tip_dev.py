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
# two small classes for simple devs, not used in tip in the moment
class Rate_Dev(object):
    def __init__(self):
        # open serial port, 9600, 8,N,1, timeout 1s
        self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
        atexit.register(self.ser.close)
    def getRate(self):
        self.ser = ser.write("R\x06")
        time.sleep(0.1)
        rate = self.ser.readline()
        #rate = self.ser.read(10) # or read 10 bytes
        #return random.random()
        return float(rate)
    
class Current_Dev(object):
    def __init__(self):
        # open serial port, 9600, 8,N,1, timeout 1s
        self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
        atexit.register(self.ser.close)
    def setCurrent(self,value):
        pass


class Heater_Dev(object):
    class dummyheater(object):
          def set_output0(self,value):
		pass
          def set_output1(self,value):
		pass

    def __init__(self,DATA):
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
			import devices.nidaq4 as nidaq
			self.HDev = nidaq
		except:
			print("NI-DAQ not found, using dummy heater.")
			self.HDev = self.dummyheater()
	
		
    def set_Heat(self,value):
        # calculate Heat for Black Fridge (R=600Ohm)
        if value < 0 :
            value = 0
        OUT_Volt = math.sqrt(value*480)
        print "Set Heat to"+str(OUT_Volt)
        return self.HDev.set_output0(OUT_Volt)

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
        self.HTR = Heater_Dev(self.DATA)
        
        #self.curr = Current_Dev()

    def run(self): 
        while True:
            if not self.DATA.Running:
                return
            #self.DATA.set_Rate(self.rate.getRate())
            R = self.RBR.get_R()
            T = self.RBR.get_T_from_R(R)
            self.DATA.set_Temp(T)
            NHW,error = self.DATA.PID.update_Heat(T)
            #print NHW,error
            # set the new heating power from pid
            self.HTR.set_Heat(NHW)
            if self.DATA.debug:
            	print "T=%.2fmK R=%.2fOhm Heat:%.4f" % (T*1000,R,NHW*1e6)
            self.DATA.set_Heat(NHW)
            self.DATA.set_pidE(error)
            self.DATA.set_last_Res(R)
            # set the next current 
            time.sleep(self.DATA.cycle_time)
            if not self.DATA.Running:
                return



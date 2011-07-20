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
                import devices.nidaq4 as nidaq
                self.HDev = nidaq
            except:
                print("NI-DAQ not found, using dummy heater.")
                self.HDev = self.dummyheater()
        else:
            pass


    def set_Heat(self,value):
        # calculate Heat for Black Fridge (R=600Ohm)
        
        if value < 0 :
            value = 0
        OUT_Volt = math.sqrt(value*self.Heater_R)
        print "Set Heat to"+str(OUT_Volt)
        # sanity check
        if OUT_Volt > 1.999:
            OUT_Volt = 1.999
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
        self.HTR = Heater_Dev(self.DATA)
        
        #self.curr = Current_Dev()

    def run(self):
        #set initial values
        BRange = self.DATA.bridge.get_Range()
        BExcitation = self.DATA.bridge.get_Excitation()
        BChannel = self.DATA.bridge.get_Channel()
        while True:
            if not self.DATA.Running:
                return
            
            # check if the range changed, this is something like an ISR
            # but polled
            if BRange != self.DATA.bridge.get_Range():
                BRange = self.DATA.bridge.get_Range()
                # set the new range, AVS47 waits 3 secs
                NR = self.RBR.set_Range(BRange)
                if NR!=BRange:
                    print "Range change failed"
            
            #update the values in the storage
            R = self.RBR.get_R()
            self.DATA.set_last_Res(R)
            T = self.RBR.get_T_from_R(R)
            self.DATA.set_Temp(T)
            ## for do not heat to much the mixing chamber
            if T > 0.7:
                self.HTR.set_Heat(0)
                self.DATA.set_ctrl_Temp(0)
                
            NHW,error = self.DATA.PID.update_Heat(T)
            # set the new heating power from pid
            HT=self.HTR.set_Heat(NHW)
            self.DATA.set_Heat(HT)
            if self.DATA.debug:
            	print "T=%.2fmK R=%.2fOhm Heat %0.4f(V) %.4f(uW)" % (T*1000,R,HT,HT**2/480*1e6)
            self.DATA.set_pidE(error)
            
            # wait for the next turn
            time.sleep(self.DATA.cycle_time)
            
            # kill thread
            if not self.DATA.Running:
                return



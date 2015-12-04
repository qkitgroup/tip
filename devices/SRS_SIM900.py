#!/usr/bin/env python

"""
SIM900 (Frame)
SIM921/SIM925(Bridge/MUX)
SIM928 (Voltage Source)
Interface SIM921 resistance bridge. HR@KIT2013, 2014, AS@KIT 2015
"""
import sys
import visa_prologix as visa

from threading import Lock

import time

import numpy as np #andre 2015-04-02
"""
exci={0:-1, 3:0, 10:1, 30:2, 100:3, 300:4, 1000:5, 3000:6, 10000:7, 30000:8}
rang={0.02:0, 0.2:1, 2:2, 20:3, 200:4, 2000:5, 20000:6, 200000:7, 2000000:8, 20000000:9}
tcon={0:-1, 0.3:0, 1:1, 3:2, 10:3, 30:4, 100:5, 300:6}

"""
class SIM900(object):
    # Fixme:port
    def __init__(self,
                 name,
                 ip="129.13.93.65",
                 gpib="GPIB::0",
                 delay = 0.2, 
                 SIM921_port=6,
                 SIM925_port=8,
                 SIM928_port=2):
        
        
        self.SIM=visa.instrument(gpib,ip=ip,delay=delay)
        self.SIM921_port = SIM921_port
        self.SIM925_port = SIM925_port
        self.SIM928_port = SIM928_port
        #  mutex locks
        self.ctrl_lock = Lock()

        print "params",ip,gpib,delay,SIM921_port,SIM925_port,SIM928_port
    def error(self,str):
        print(str)
    
    def setup_device(self):
        pass
    def SIM_prolog(self,port = 0, init = False):
        try:
            # commands to mainframe
            self.SIM.write('main_esc')
            # flush output queue of SIM900
            self.SIM.write('FLOQ')
            if init:
                self.SIM.write('*CLS')
                self.SIM.write('*RST')
                self.SIM.write('CEOI ON') 
                self.SIM.write('EOIX ON')
            self.SIM.write('CONN '+str(port)+', "main_esc"')
        except:
            self.error('No Connection to SIM900 MAINFRAME up to main_esc')
    
    def SIM_epilog(self):
        self.SIM.write('main_esc')
    
    def get_value_from_SIM900(self,port,cmd):
        with self.ctrl_lock:
            for i in range(50): #try 50 times, Andre 2015-05-31
                try:
                    self.SIM_prolog(port)
                    val = self.SIM.ask(str(cmd))
                    #float(val) #only to catch the error, if this can not be converted to float #but not all are float!
                    self.SIM_epilog()
                    return val
                except Exception as e:
                    print ">>>Error #%i,%s: trying again '%s' on port %i"%(i,e,cmd,port)
                    time.sleep(.5)
                    continue
            return False
    def set_value_on_SIM900(self,port,cmd):
        with self.ctrl_lock:
            self.SIM_prolog(port)
            self.SIM.write(str(cmd))
            self.SIM_epilog()
    
    def _get_IDN(self,port):
        cmd = "*IDN?"
        return (self.get_value_from_SIM900(port,cmd)).strip()
        
        
    def get_Rval(self):
        port  = self.SIM921_port
        cmd = 'RVAL?'
        for i in range(3):
            try: #andre 2015-04-02
                return float(self.get_value_from_SIM900(port,cmd))
            except ValueError:
                continue
        return np.nan
        
    def _get_ave(self):
        return np.mean([self.get_Rval() for i in range (5)])
    def _set_local(self):
        pass
    def _close(self):
        pass

    def _get_Channel(self):
        port  = self.SIM925_port
        cmd = "CHAN?"
        try:
            return int(self.get_value_from_SIM900(port,cmd))
        except ValueError:
            print "Value Error at get_channel, channel may not be set correctly"
            return False
    
    def _set_Channel(self,channel):
        port  = self.SIM925_port
        cmd = "CHAN%i;CHAN?"%(channel)
        try:
            return int(self.get_value_from_SIM900(port,cmd))
        except ValueError:
            print "Value Error at set_channel, channel may not be set correctly"
            return False
        ########################################################
        # commands for the SIM298 isolated voltage source
        # (likely to be used as a heater ;-) )
        ########################################################
    def get_Voltage(self):
            port = self.SIM928_port
            cmd = "VOLT?"
            try:
               return float(self.get_value_from_SIM900(port,cmd))
            except ValueError:
               print "Value Error at get_Voltage, channel may not be set correctly"
               return False
    def set_Voltage(self,voltage):
           port = self.SIM928_port
           cmd = "VOLT "+str(voltage)
           self.set_value_on_SIM900(port,cmd)
    def set_output0(self,OUT_Volt): # HEATER interface
           self.set_Voltage(OUT_Volt)
    def set_output_ON(self):
           port = self.SIM928_port
           cmd = "OPON; EXON?"
           return self.get_value_from_SIM900(port,cmd)
    def set_output_OFF(self):
           port = self.SIM928_port
           cmd = "OPOF; EXON?"
           return self.get_value_from_SIM900(port,cmd)
    
    def _set_Excitation(self,ex):
        port  = self.SIM921_port
        #cmd = "EXCI %i;EXCI?"%(ex)
        #return int(self.get_value_from_SIM900(port,cmd))
        cmd = "EXCI %i"%(ex)
        self.set_value_on_SIM900(port,cmd)
    def _set_Range(self,range):
        port  = self.SIM921_port
        #cmd = "RANG%i;RANG?"%(range)
        #return int(self.get_value_from_SIM900(port,cmd))
        cmd = "RANG%i"%(range)
        self.set_value_on_SIM900(port,cmd)

if __name__ == "__main__":
    # port 6 is the port to the SRS SIM921 bridge, port 8 is the SIM925 multiplexer
    SIM=SIM900("SIM900") 
    print SIM._get_IDN(8)
    print SIM._get_IDN(2)
    print SIM._get_Channel()
    print SIM.get_Rval()
    print SIM._get_ave()

    #SIM._close_connection()


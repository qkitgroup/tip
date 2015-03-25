#!/usr/bin/env python
# TIP DATA class version 0.2 written by HR@KIT Dec 2011
# to do
# make the _whole_ thing thread safe.

import numpy
import thread
from threading import Lock
try:
    import cPickle as pickle
except:
    import pickle


# DATA exchange class, also holds global variables for
# Thread management

class DATA(object):
    class remote_info(object):
        last_Temp=0
        last_pidE=0
        last_Heat=0

    class LOCALHOST(object):
        def __init__(self,config):
            self.name = config.get('LOCALHOST','name')
            self.ip   = config.get('LOCALHOST','ip')
            self.port = config.getint('LOCALHOST','port')
            self.valid_IPs = config.get('LOCALHOST','valid_IPs').split(",") 
    class REMOTEHOST(object):
        def __init__(self,config):
            self.name = config.get('REMOTEHOST','name')
            self.ip   = config.get('REMOTEHOST','ip')
            self.port = config.getint('REMOTEHOST','port')
    class BRIDGE(object):
        def __init__(self,config):
            self.range = config.getint('RBridge','default_range')
            self.excitation = config.getint('RBridge','default_excitation')
            self.channel = config.getint('RBridge','default_channel')
            # management
            self.bridge_lock = Lock()
            self.tainted = False
            
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
        
        def set_Channel(self,Channel):
            with self.bridge_lock:
                self.tainted = True
                self.channel = Channel
                return(1)
        def get_Channel(self):
            return self.channel

    class HEATER(object):
        def __init__(self,config):
            self.Resistor = config.getfloat('Heater',"Resistor")

    def __init__(self,config):
        # tip variables
        self.Running = True
        self.wants_abort = False
        self.debug = True
        self.cycle_time = 0.5

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
        self.localhost  = self.LOCALHOST(config)
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
        
        
        
class GUI_DATA(object):
    def __init__(self):
        # tip variables
        self.Running = True
        self.wants_abort = False
        self.debug = True
        self.cycle_time = 0.5
        

if __name__ == "__main__":
    DATA = DATA()

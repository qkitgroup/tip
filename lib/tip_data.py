#!/usr/bin/env python
# TIP DATA class version 0.1 written by HR@KIT Dec 2010

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
	


    def __init__(self):
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
        self.config = ""
        self.ctrl_PID = (0.04,0.04,0)
	self.ctrl_T = 0
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

    def set_Heat(self,heat):
	lock = Lock()
	with lock:
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
if __name__ == "__main__":
    DATA = DATA()

#!/usr/bin/env python

"""
Dummy resistance bridge
"""
import sys
import random

from threading import Lock

import time


class DummyDevice(object):
    # Fixme:port
    def __init__(self,
                 name,
                 ):
        self.ctrl_lock = Lock()

    def error(self,str):
        print(str)
    
    def setup_device(self):
        pass
    
    
    def _get_IDN(self,port):
        return "Dummy Bridge v0"
        
    def get_measured_value(self,params):
        """ This is the main function for TIP 2 
        params is a object describing the measurement
        containing for instance (resistance bridge):
            channel
            excitation
            range
            integration time
        and returns the measured value
        """
        return 0


    def get_Rval(self):
        return random.random()*100+10000
        
    def _get_ave(self):
        return np.mean([self.get_Rval() for i in range (5)])
    def _set_local(self):
        pass
    def _close(self):
        pass
    def get_Channel(self): return 0
    def _get_Channel(self): return 0
    def set_Channel(self,channel): pass
    def _set_Channel(self,channel): pass
    def set_Excitation(self,ex): pass
    def _set_Excitation(self,ex): pass
    def set_Eange(self,range): pass    
    def _set_Range(self,range): pass

if __name__ == "__main__":
    
    RBR=DummyDevice("dumm")
    print (RBR.get_Channel())
    
    

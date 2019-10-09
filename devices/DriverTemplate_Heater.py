#!/usr/bin/env python

"""
Dummy heater driver / basic interface
"""
import sys
import random
import time


class driver(object):
    
    def __init__(self,name):
        pass
    
    def setup_device(self):
        pass
    
    def get_idn(self):
        return( "Dummy HEater  ... v0" )
        
    def get_heater_power(self):
        # random number
        return random.random()*100+10000
    def set_heater_power(self,value):
        pass

    def get_heater_channel(self):
        return 0
    def set_heater_channel(self,value):
        pass

    def set_local(self):pass
    def close(self):pass

if __name__ == "__main__":
    
    ht=driver("DebugHeater")
    print (ht.get_heat())
    print (ht.set_heat(2.0))
    
    

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
        
    def get_heat(self):
        # random number
        return random.random()*100+10000
    def set_heat(self,value):
        pass
 
    def set_local(self):pass
    def close(self):pass

if __name__ == "__main__":
    
    ht=driver("DebugHeater")
    print (ht.get_heat())
    print (ht.set_heat(2.0))
    
    

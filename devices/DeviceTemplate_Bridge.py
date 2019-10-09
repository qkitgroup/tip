#!/usr/bin/env python

"""
Dummy resistance bridge driver /  basic interface
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
        return( "Dummy Bridge  ... v0" )
        
    def get_resistance(self):
        """ This is the main function for TIP 2 
        params is a object describing the measurement
        containing for instance (resistance bridge):
            channel
            excitation
            range
            integration time
        and returns the measured value
        """
        # random number
        return random.random()*100+10000
 
    def get_channel(self): return 0
    def set_channel(self,channel): pass

    def get_excitation(self): return 0 
    def set_excitation(self,excitation): pass

    def get_range(self): return 0
    def set_range(self,range): pass
    
    def set_local(self):pass
    def close(self):pass

if __name__ == "__main__":
    
    br=driver("DebugBridge")
    print (br.get_resistance())
    print (br.get_channel())
    
    

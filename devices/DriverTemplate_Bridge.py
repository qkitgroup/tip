#!/usr/bin/env python

"""
Dummy resistance bridge driver /  basic interface
"""
import sys
import random
import time
from lib.tip_config import config

def driver(name):
    DT = DriverTemplate(name)
                
    config[name]['device_ranges'] = DT.ranges
    config[name]['device_excitations'] = DT.excitations
    return DT

class DriverTemplate(object):
    
    def __init__(self,name):
        # bridge ranges v 0    v 1    ...                            v 7    
        self.ranges = [ 'None', '2R', '20R','200R','2K','20K','200K','2M']
        # bridge excitations v 0    v 1    ...                                           v 7
        self.excitations = ['None','3 uV', '10 uV', '30 uV', '100 uV', '300_uV', '1 mV', '3 mV']
        
    
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
        time.sleep(self.integration_time)
        return random.random()*100+10000
 
    def get_channel(self): return 0
    def set_channel(self,channel): pass

    def get_excitation(self): return 0 
    def set_excitation(self,excitation): pass

    def get_range(self): return 0
    def set_range(self,range): pass

    def set_integration(self,time): 
        self.integration_time = time
        
    
    def set_local(self):pass
    def close(self):pass

if __name__ == "__main__":
    
    br=driver("DebugBridge")
    print (br.get_resistance())
    print (br.get_channel())
    
    

#!/usr/bin/env python

"""
driver for the tinkerforge humidity bricklet v2 /  basic interface
drivers e.g. through
pip install tinkerforge
"""
import sys
import random
import time
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_humidity_v2 import BrickletHumidityV2
from lib.tip_config import config

def driver(name):
    dev = TF_BrickletHumidity(name,
    config[name]['device_uid'],
    config[name].get('device_host','localhost'),
    config[name].get('device_port',4223)
    )
    #config[name]['device_uid'] = DT.ranges
    #config[name]['device_excitations'] = DT.excitations
    return dev

class TF_BrickletHumidity(object):
    
    def __init__(self,name,uid,host="localhost", port = 4223):
        self.uid  = uid
        self.host = host
        self.port = port 
        self.setup_device()
    
    def setup_device(self):
        self.ipcon = IPConnection() # Create IP connection
        self.hd = BrickletHumidityV2(self.uid, self.ipcon) # Create device object
        self.ipcon.connect(self.host, self.port) # Connect to brickd
        # moving average over the last 60 seconds
        self.hd.set_moving_average_configuration(60, 60)
    
    def get_idn(self):
        return( "TF_BrickletHumidity UID: " + self.uid)
        
    def get_humidity(self):

        """ 
        """
        return self.hd.get_humidity()/100.0 # in %

    def get_temperature(self):

        """ 
        """
        return self.hd.get_temperature()/100.0 # in DEG C

    def get_channel(self): return 0
    def set_channel(self,channel): pass

    def get_excitation(self): return 0 
    def set_excitation(self,excitation): pass

    def get_range(self): return 0
    def set_range(self,range): pass

    def set_integration(self,time): 
        self.integration_time = time
        
    
    def set_local(self):pass

    def close(self):
        ipcon.disconnect()

if __name__ == "__main__":
    
    dev = TF_BrickletHumidity('test','Loy')
    print (dev.get_humidity())
    print (dev.get_temperature())

#!/usr/bin/env python

"""
Driver for the PREVAC Synthesium Software, which is based on a TANGO object dispatcher. 

"""
import os
import tango
from lib.tip_config import config

def driver(name):
    drv  =  PREVAC_Tango(name)
    drv.setup_device(TANGO_HOST = config[name]['address'], 
                     TANGO_PORT = config[name]['port'])
    return drv

class PREVAC_Tango(object):
    
    def __init__(self,name):
        self.tango_device = ""
        self.tango_device_id = ""
    
    def setup_device(self,TANGO_HOST = "TANGO_HOST",TANGO_PORT = 20000):
        self.tango_host = f"{TANGO_HOST}:{TANGO_PORT}"
        os.environ['TANGO_HOST'] = self.tango_host
        tango.ApiUtil.get_env_var("TANGO_HOST") 
    
    def get_idn(self):
        return( f"{self.tango_device_id} on TANGO server {self.tango_host}" )

    def set_tango_device(self,device_uid):
        self.tango_device_id = device_uid
        self.tango_device = tango.DeviceProxy(self.tango_device_id)

    def get_pressure(self):
        try:
            p = self.tango_device.value
            # print(f'Pressure {p:.3e} mbar')
            
            # sometimes the gauges return an underrange value = 0
            if p == 0: 
                return None
            else:
                return p
            
        except ValueError:
            # value is e.g. raised when no gauge is connected
            # this way we can still ask vor a value and then live with a None response
            return None


    def close(self):
        pass

if __name__ == "__main__":
    
    dpg=PREVAC_Tango()
    dpg.setup_device()
    for a in range(0,9): 
        print(a)
        try:
            dpg.set_channel(a)
            p = dpg.get_pressure()
            print(f"type {dpg.get_gauge_type(a)}")
        except ValueError:
            # no response from the gauge -> probably nothing connected
            pass
    

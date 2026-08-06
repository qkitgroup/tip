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
    
    def setup_device(self,TANGO_HOST = "127.0.0.1",TANGO_PORT = 20000):
        # The TANGO_HOST environment variable directs TANGO to the server 
        # However, when it is reset by the python driver it stalls up to 12 s
        # so we only set it if required 
        self.tango_host = f"{TANGO_HOST}:{TANGO_PORT}"
        tango_host_env = tango.ApiUtil.get_env_var("TANGO_HOST")
        #print (f"#{self.tango_host}##{tango_host_env}#") 
        if tango_host_env == self.tango_host:
            #print (" TANGO_HOST not set")
            pass
        else:
            os.environ['TANGO_HOST'] = self.tango_host
            #print ("TANGO_HOST reset")
            pass

    
    def get_idn(self):
        return( f"{self.tango_device_id} on TANGO server {self.tango_host}" )

    def set_tango_device(self,device_uid):
        self.tango_device_id = device_uid
        self.tango_device = tango.DeviceProxy(self.tango_device_id)

    def get_pressure(self):
        try:
            p = self.tango_device.value
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
    d = 'synthesium/gaugevalues/spc_bara'
    tg=PREVAC_Tango("test")
    tg.setup_device()
    print ("setup_device done")
    tg.set_tango_device(d)
    print ("set_tango_device done")
    for i in range(10):
        p = tg.get_pressure()
        print(f"Pressure on device {d} is {p}")

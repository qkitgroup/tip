#!/usr/bin/env python

"""
Pfeiffer DPG 109 Display controller for digital vacuum gauges
"""
#import sys
#import time
import serial
import pfeiffer_vacuum_protocol as pvp

#import tip.config

def driver():
    drv  =  Pfeiffer_DPG109("name")
    drv.setup_device()
    return drv

class Pfeiffer_DPG109(object):
    
    def __init__(self,name):
        pass
    
    def setup_device(self,serial_dev = "/dev/ttyUSB0"):
        self.con = serial.Serial(serial_dev, timeout=1)
    
    def get_idn(self):
        return( "None" )
    
    def get_pressure(self,channel):
        p = pvp.read_pressure(self.con, channel)
        print(f'Pressure {p:.3e} mbar')
        return p

    def get_gauge_type(self,channel):
        return pvp.read_gauge_type(self.con,channel)

    def close(self):
        pass

if __name__ == "__main__":
    
    dpg=Pfeiffer_DPG109("DPG109")
    dpg.setup_device()
    for a in range(0,9): 
        print(a)
        try:
            p = dpg.get_pressure(a)
            print(f"type {dpg.get_gauge_type(a)}")
        except ValueError:
            # no response from the gauge -> probably nothing connected
            pass
    

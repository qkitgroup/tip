#!/usr/bin/env python
# HR@KIT (2024)
# tip driver for the Leybold combivac cm31 vacuum pressure controller


import serial
import time
from lib.tip_config import config

def driver(name):
    drv  =  Leybold_combivac(name)
    drv.setup_device(serial_dev = config[name]['address'])
    return drv

class Leybold_combivac(object):
    
    def __init__(self,name):
        self.ack=b'\x06\r'
        self.nak=b'\x15\r'
        self.channel = 0
    
    def setup_device(self,serial_dev = "/dev/ttyUSB0"):
        baudrate = 2400 # 8N1
        timeout = 0.1
        self.con = serial.Serial(serial_dev, baudrate, timeout=timeout)
        #self.address = self.get_Address_Transducer()
    
    def remote_cmd(self,cmd):
        cmd+=b"\r"

        # clear queue first, old data,etc
        rem_char = self.con.inWaiting()
        if rem_char:
            self.con.read(rem_char)
        
        # send command
        self.con.write(cmd)
        # wait until data is processed
        time.sleep(0.5)
        # read back
        rem_char = self.con.inWaiting()
        #print (f"read chars {rem_char}")
        #print (f"reply: {self.con.read(rem_char)}")
        ack = self.con.read(2)
        if ack == self.ack:
            time.sleep(0.5)
            rem_char = self.con.inWaiting()
            value = self.con.read(rem_char)
            return value
        else:
            print("error in reading")
            return None

        
        
    
    def get_pressure(self):
        channels = ['TM1', 'TM2', 'PM1']
        try:
            # channel is one in [ TM1, TM2, PM1 ]
            rcmd = f"MES R {channels[self.channel]}".encode()
            p = (self.remote_cmd(rcmd).decode().split(':')[-1])
            
            # sometimes the gauge is off or  return an underrange value = 0
            if p == 'OFF\r': 
                return None
            else:
                return float(p)
            
        except (ValueError, AttributeError):
            # value is e.g. raised when no gauge is connected
            # this way we can still ask vor a value and then live with a None response
            return None

    def get_idn(self):
        return( "" )

    def set_channel(self,channel):
        self.channel = channel

    def close(self):
        pass

if __name__ == "__main__":
    
    dpg=Leybold_combivac("pdf")
    dpg.setup_device(serial_dev = "/dev/ttyUSB0")
    dpg.set_channel(0)
    print (f"TM1: {dpg.get_pressure()} mBar")
    dpg.set_channel(1)
    print (f"TM2: {dpg.get_pressure()} mBar")
    dpg.set_channel(2)
    print (f"PM1: {dpg.get_pressure()} mBar")
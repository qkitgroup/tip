#!/usr/bin/env python
# HR@KIT (2024)
# tip driver for the MKS PDR900 vacuum pressure gauges


import serial
import time
from lib.tip_config import config

def driver(name):
    drv  =  MKS_PDF900(name)
    drv.setup_device(serial_dev = config[name]['address'])
    return drv

class MKS_PDF900(object):
    
    def __init__(self,name):
        self.ack="ACK"
        self.nak="NAK"
        self.channel = 0
    
    def setup_device(self,serial_dev = "/dev/ttyUSB0"):
        baudrate = 9600
        timeout = 0.1
        self.con = serial.Serial(serial_dev, baudrate, timeout=timeout)
        self.address = self.get_Address_Transducer()
    
    def remote_cmd(self,cmd):
        cmd+=b"\n"

        # clear queue first, old data,etc
        rem_char = self.con.inWaiting()
        if rem_char:
            self.con.read(rem_char)
        
        # send command
        self.con.write(cmd)
        # wait until data is processed
        time.sleep(0.2)
        # read back
        rem_char = self.con.inWaiting()
        value = self.con.read(rem_char)
        return value
                
    #controller 
    def get_Serial_Controller(self):
        rcmd = f"@{self.address:0>3}SNC?;FF".encode()
        return self.remote_cmd(rcmd)[7:-3]
        #return self.remote_cmd(b"@001SNC?;FF")
    def get_Address_Controller(self):
        rcmd = f"@{self.address:0>3}ADC?;FF".encode()
        return self.remote_cmd(rcmd)
        #return (self.remote_cmd(b"@254ADC?;FF"))
        
    #transducer 
    def get_Baud_Transducer(self):
        rcmd = b"@xxxBR?;FF"
        return self.remote_cmd(rcmd)[7:-3]
        #return self.remote_cmd(b"@xxxBR?;FF")
    def get_Address_Transducer(self):
        rcmd = b"@xxxAD?;FF"
        return int(self.remote_cmd(rcmd)[7:10])
        #return int(self.remote_cmd(b"@xxxAD?;FF"))
    
    def get_pressure(self):
        try:
            #p = float(self.remote_cmd(f"@{self.address}PR3?;FF")[7:14])
            rcmd = f"@{self.address:0>3}PR3?;FF".encode()
            p = float(self.remote_cmd(rcmd)[7:14])
            print(f'Pressure {p:.3e} mbar')
            
            # sometimes the gauges return an underrange value = 0
            if p == 0: 
                return None
            else:
                return p
            
        except ValueError:
            # value is e.g. raised when no gauge is connected
            # this way we can still ask vor a value and then live with a None response
            return None
        
    def setAddressT(self,address = "002"):
        return self.remote_cmd("@xxxAD!" + address + ";FF")
    
    def get_idn(self):
        return( "" )

    def set_channel(self,channel):
        self.channel = channel
    
    def read_pressure(connection, channel):
        pressure = 0
        return pressure

    def close(self):
        pass

if __name__ == "__main__":
    
    dpg=MKS_PDF900("pdf")
    dpg.setup_device(serial_dev = "/dev/ttyUSB2")
    print(f"Address Transducer {dpg.get_Address_Transducer()}")
    print(f"Address Controller {dpg.get_Address_Controller()}")
    print(f"Baud Tranducer {dpg.get_Baud_Transducer()}")
    print(f"Serial Controller {dpg.get_Serial_Controller()}")
    p = dpg.get_pressure()

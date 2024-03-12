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
    #for a in range(0,9): 
    #    print(a)
    #    try:
    #dpg.set_channel(a)
    print(f"Address Transducer {dpg.get_Address_Transducer()}")
    print(f"Address Controller {dpg.get_Address_Controller()}")
    print(f"Baud Tranducer {dpg.get_Baud_Transducer()}")
    print(f"Serial Controller {dpg.get_Serial_Controller()}")
    p = dpg.get_pressure()
    #        #print(f"type {dpg.get_gauge_type(a)}")
    #    except ValueError:
    #        # no response from the gauge -> probably nothing connected
    #        pass

""" 
import time,sys
import atexit

class Pressure_Dev(object): 
    def __init__(self,device_sel = "pl1_MC"):
        '''
        instantiate passing a parameter device_sel, which is one of
        pl1_LL, pl1_MC, AlOx_LL or directly a valid serial device
        '''

        self.ack="ACK"
        self.nak="NAK"
        baudrate = 9600
        timeout = 0.1
        
        if device_sel == "pl1_LL":
            device = "/dev/ttyUSB2"
        elif device_sel == "pl1_MC":
            device = "/dev/ttyUSB1"
        elif device_sel == "AlOx_LL":
            device = "/dev/ttyUSB4"
        else:
            if '/dev/ttyUSB' in device_sel:
                device = device_sel
            else:
                print "Error loading MKS PDR900 instrument: Device not recognized."
                raise ValueError
       
        self.ser = self._std_open(device,baudrate,timeout)
        atexit.register(self.ser.close)
        
    def _std_open(self,device,baudrate,timeout):
        import serial
        # open serial port, 9600, 8,N,1, timeout 0.1
        return serial.Serial(device, baudrate, timeout=timeout)
        
    def remote_cmd(self,cmd):
        cmd+="\n"

        # clear queue first, old data,etc
        rem_char = self.ser.inWaiting()
        if rem_char:
            self.ser.read(rem_char)
        
        # send command
        self.ser.write(cmd)
        # wait until data is processed
        time.sleep(0.2)
        # read back
        rem_char = self.ser.inWaiting()
        value = self.ser.read(rem_char)
        return value
        
    #due to compatibility...
    def getTM1(self):
        return self.getPressure(self.getAddressT())
    def getTM2(self):
        return self.getPressure(self.getAddressT())
    def getUHV(self):
        return self.getPressure(self.getAddressT())
                
    #controller methods
    def getSerial(self):
        return self.remote_cmd("@001SNC?;FF")[7:-3]
    def getAddress(self):
        return self.remote_cmd("@254ADC?;FF")
        
    #transducer methods
    def getBaudT(self):
        return self.remote_cmd("@xxxBR?;FF")[7:-3]
    def getAddressT(self):
        return self.remote_cmd("@xxxAD?;FF")[7:10]
    def getPressure(self,address=None):
        try:
            if not address:
                address = self.getAddressT()
            return self.remote_cmd("@" + address + "PR3?;FF")[7:14]
        except Exception as m:
            print m
            return 0
        
    def setAddressT(self,address = "002"):
        return self.remote_cmd("@xxxAD!" + address + ";FF")
        
                
if __name__ == "__main__":
    pMC = Pressure_Dev("pl1_MC")
    print "Baudrate Transducer MC: ", pMC.getBaudT()
    addrMC = str(pMC.getAddressT())    #transducer address
    print "Pressure MC: ", pMC.getPressure(addrMC)
    
    pLL = Pressure_Dev("pl1_LL")
    print "Baudrate Transducer LL: ", pLL.getBaudT()
    addrLL = str(pLL.getAddressT())    #transducer address
    print "Pressure LL: ", pLL.getPressure(addrLL)
"""

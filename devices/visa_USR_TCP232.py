#!/usr/bin/env python
"""
serial_ETHERNET python class for USR TCP232 bridge, 
written by Hannes Rotzinger, rotzinger@kit.edu for TIP but 
can also be used in combination with visa

interfaces serial (RS232, RS485) commands over ethernet

released under the GPL, whatever version

Changelog:
0.1 12.2022 initial version, adopted from visa_prologix
"""

import socket
import time
import logging

class instrument(object):
    
          
    """ for serial ethernet bridge """
    def __init__(self,ident,**kwargs):

        #
        # ethernet socket to connect to the USR TCP232-ETHERNET 
        #
        self.sock = None

        # IP address and port of the USR TCP323 ETHERNET
        self.ip = kwargs.get("ip","")

        self.ethernet_port = kwargs.get("port", 1234)

        # for compatibility with NI visa

        #
        # timeout of the  USR TCP232-ETHERNET device while 
        # reading from the instrument
        #
        self.timeout        = kwargs.get("timeout",3)

        #
        # delay after each write command to the device 
        # 
        self.delay          = kwargs.get("delay",0.1)
        
        #
        # size of chunks read
        # 
        self.chunk_size     = kwargs.get("chunk_size",4096)

        #
        # values format
        # 
        self.values_format  = kwargs.get("values_format",'ascii')

        #
        # End of message char, possible values "\n","\r","\r\n",""
        #
        self.term_char      = kwargs.get("term_char","\n")

        #
        # the eos_char is used to determine the end of a message
        # while reading. Possible values are '\r\n', '\r', '\n', ''
        #
        self.eos_char       = kwargs.get("eos_char","")

        #
        # some instruments are very slow in responding. 
        # this is an additional delay between a write and a read
        #
        self.instrument_delay = kwargs.get("instrument_delay",0)

        self.send_end       = kwargs.get("send_end", False)
        
        # enable/disable debugging
        self.debug          =  kwargs.get("debug",   False)
        if self.debug:
            logger = logging.getLogger()
            logger.setLevel(logging.DEBUG)

        #
        # setup of the USR TCP232-ETHERNET
        #

        # open connection
        self._open_connection()

        
        self._set_read_timeout(self.timeout)

        
        

    # wrapper functions for py visa
    def write(self,cmd):
        return self._send(cmd)
    def read(self):
        return self._recv()
    def read_values(self,format):
        #
        # FIXME: not yet implemented: format
        #
        return self._recv()
        
    def ask(self, cmd, instrument_delay = 0):
        return self._send_recv(cmd, instrument_delay)

    def ask_for_values(self,cmd,format=None,instrument_delay = 0):
        #
        # FIXME: not yet implemented: format
        #
        return self._send_recv(cmd,instrument_delay)
        
    def clear(self):
        return self._set_reset()
    def trigger(self):
        return self._set_trigger()

    # this is in the Gpib class of pyvisa, has to move there later
    def send_ifc(self):
        return self._set_ifc()
    
    # 
    # internal commands to access the USR TCP232 device
    #
    
    def _send(self,cmd):
        "send data to device"

        cmd += self.term_char
        cmd  = cmd.encode('ascii')

        logging.debug("VISA USR232 CMD: " + str(cmd))
        self.sock.send(cmd)
        #sock.sendall(cmd)
        # wait for delay seconds before next command. 
        # depends on the device
        time.sleep(self.delay)
        

    def _recv(self,**kwargs):
        # read data from device, remove the trailing non-printable chars
        # and convert it to a utf8 string
        
        data = self.sock.recv(self.chunk_size)
        return data.decode().rstrip()
        
    def _send_recv(self,cmd,instrument_delay=0,**kwargs):
        "send and read"
        
        self._send(cmd)

        time.sleep(instrument_delay)

        return self._recv()
    
    def _open_connection(self):
        # Open TCP connect to port of USR-TCP232-ETHERNET
        self.sock = socket.socket(
            socket.AF_INET, 
            socket.SOCK_STREAM, 
            socket.IPPROTO_TCP)

        self.sock.settimeout(self.timeout)
        self.sock.connect((self.ip, self.ethernet_port))

    def _close_connection(self):
        self.sock.close()
        
            
    def _set_read_after_write(self, On=True):
        pass

    def _set_read_timeout(self,timeout):
        # sets the timeout of the device before reading.
        pass
    
    #
    # lower level functions, may not be neccessary
    #

    def _get_status(self):
       
        return self._recv(self.chunk_size)
    
    def _set_reset(self):
        # Reset Device  endpoint
        self._send("")        
       
    def _set_dev_reset(self):
        # Reset Device  endpoint
        self._send("*RST")        
        
    def _get_idn(self):
        return self._send_recv("*IDN?",instrument_delay=self.instrument_delay)

    def _get_version(self):
        return None

    # generic error class
    class Error(Exception):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return repr(self.value)
    
    


# do some checking ...
if __name__ == "__main__":
    dev=instrument(
        "HPdev", 
        ip = "192.168.0.7",
        port = 8000,  
        delay = 0.05, 
        term_char = "\n",
        eos_char = "",
        timeout = 1,
        instrument_delay = 0,
        debug = True
        )

    #dev.write("*ESE 1")
    #dev.write("*SRE 32")
    #dev.write("HDR 0")
    #dev.write("*OPC")
    for i in range(10):
        print(dev.ask("*IDN?"))

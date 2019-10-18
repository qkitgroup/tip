#!/usr/bin/env python
"""
GPIB_ETHERNET python class for prologix ethernet-to-gpib bridge, 
written by Hannes Rotzinger, hannes.rotzinger@kit.edu for TIP but 
can also be used in combination with visa

interfaces GPIB commands over ethernet

released under the GPL, whatever version

Changelog:
0.1 March 2010 (HR), initial version, very alpha, most of the functionality is far from bullet proof.
0.2 Oct. 2019 (HR), mayor update 
"""

import socket
import time
import re
import logging

class instrument(object):
    
          
    """ for prologix gpib_ethernet bridge """
    def __init__(self,gpib,**kwargs):

        #
        # ethernet socket to connect to the PROLOGIX GPIB-ETHERNET 
        #
        self.sock = None

        # IP address and port of  PROLOGIX GPIB-ETHERNET
        self.ip = kwargs.get("ip","")

        self.ethernet_port = kwargs.get("port", 1234)

        # for compatibility with NI visa

        #
        # timeout of the PROLOGIX GPIB-ETHERNET device while 
        # reading from the instrument
        #
        self.timeout        = kwargs.get("timeout",3)

        #
        # delay after each write command to the PROLOGIX GPIB-ETHERNET 
        # device
        # 
        self.delay          = kwargs.get("delay",0.1)
        
        #
        # size of chunks read
        # 
        self.chunk_size     = kwargs.get("chunk_size",20*1024)

        #
        # values format
        # 
        self.values_format  = kwargs.get("values_format",'ascii')

        #
        # End of message char, possible values "\n","\r","\r\n",""
        #
        self.term_char      = kwargs.get("term_char","")

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
        
        self.debug          =  kwargs.get("debug",   False)

        #
        # setup of the PROLOGIX GPIB-ETHERNET
        #

        # parse gpib address (throws an Error() if fails)
        self.gpib_addr      = self._get_gpib_adr_from_string(gpib)

        # open connection
        self._open_connection()

        # set the GPIB address of the device
        self._set_gpib_address()

        if self.send_end:
            self._set_EOI_assert()

        # disable the automatic saving of parameters in
        # the ethernet-gpib device,
        self._set_saveconfig(False)
        
        # set set the ethernet gpib device to be the controller of#
        # the gpib chain
        self._set_controller_mode()
        
        # switch automatic receive off
        self._set_read_after_write(False)        

        self._set_EOI_assert(True)
        
        self._set_read_timeout(self.timeout)

        # append TERM CHAR at the end.
        self._set_GPIB_EOS(self.eos_char)

        

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

    # utility functions
    def _get_gpib_adr_from_string(self,gpib_str):
        # very,very simple GPIB address extraction.
        p = re.compile('(gpib::|GPIB::)(\d+)')
        m = p.match(gpib_str)
        if m:
            return int(m.group(2))
        else:
            raise self.Error("Only GPIB:: is supported!")

    # 
    # internal commands to access the prologix gpib device
    #
    
    def _send(self,cmd):
        "send data to device"

        cmd += self.term_char
        cmd  = cmd.encode('ascii')

        logging.debug("VISA PROLOGIX CMD: " + str(cmd))
        self.sock.send(cmd)
        # wait for delay seconds before next command. 
        # depends on the device
        time.sleep(self.delay)

    def _recv(self,**kwargs):
        "read data from device"
        bufflen=kwargs.get("bufflen",self.chunk_size)

        self._set_read()
        
        buff = self.sock.recv(bufflen)
        return buff
        
    def _send_recv(self,cmd,instrument_delay=0,**kwargs):
        "send and read "
        bufflen=kwargs.get("bufflen",self.chunk_size)

        self._send(cmd)

        time.sleep(instrument_delay)

        return self._recv(bufflen=bufflen)
    
    def _set_read(self):
        "put prologix device into the *read* state"

        EOS_chars={'\r\n':'10', '\r':'13', '\n':'10', '':'eoi'}

        self._send("++read "+EOS_chars[self.eos_char])
        # examples:
        #self._send("++read eoi")
        #self._send("++read 10") #LFs
        #self._send("++read 13") #CR


    def _open_connection(self):
        # Open TCP connect to port 1234 of GPIB-ETHERNET
        self.sock = socket.socket(
            socket.AF_INET, 
            socket.SOCK_STREAM, 
            socket.IPPROTO_TCP)

        self.sock.settimeout(self.timeout)
        self.sock.connect((self.ip, self.ethernet_port))

    def _close_connection(self):
        self.sock.close()
        
    def _set_saveconfig(self,On=False):
        # should not be used very frequently
        if On:
            self._send("++savecfg 1")
        else:
            self._send("++savecfg 0")
            
    def _set_gpib_address(self,**kwargs):
        # GET GPIB address
        self.gpib_addr = kwargs.get("gpib_addr",self.gpib_addr)
        # SET GPIB address on the device
        self._send("++addr " + str(self.gpib_addr))

    def _set_controller_mode(self,C_Mode=True):
        # set gpib_ethernet into controller mode (True) or in device mode (False)
        if C_Mode:
            # controller mode
            self._send("++mode 1")
        else:
            # device mode
            self._send("++mode 0")
            
    def _set_read_after_write(self, On=True):
        if On:
            # Turn on read-after-write
            self._send("++auto 1")
        else:
            # Turn off read-after-write to avoid "Query Unterminated" errors
            self._send("++auto 0")

    def _set_read_timeout(self,timeout):
        # sets the timeout of the device before reading.
        self._send("++read_tmo_ms "+str(int(timeout*1000)))
    
    #
    # lower level functions, may not be neccessary
    #


    def _set_EOI_assert(self,On=True): #
        # Assert EOI signal line with last byte to indicate end of data
        if On:
            self._send("++eoi 1")
        else:
            self._send("++eoi 0")
            
    def _set_GPIB_EOS(self,EOS=''): 
        # end of signal/string, default is None
        EOSs={'\r\n':0,'\r':1,'\n':2,'':3}
        self._send("++eos "+str(EOSs[EOS]))

    def _set_GPIB_EOT(self,EOT=False):
        # send at EOI an EOT (end of transmission) character ?
        if EOT:
            self._send("++eot_enable 1")
        else:
            self._send("++eot_enable 0")
    def _set_GPIB_EOT_char(self,EOT_char=42):
        # set the EOT character
        self._send("++eot_char"+EOT_char)

    def _set_ifc(self):
        self._send("++ifc")

    # get the service request bit
    def _get_srq(self,**kwargs):
        cmd="++srq"
        self._send(cmd)
        return self._recv()

    def _get_spoll(self):
        cmd="++spoll"
        return self._send_recv(cmd,instrument_delay=0.4).rstrip()
    
    def _get_status(self):
        cmd="++status 48"
        #cmd=cmd.rstrip()
        cmd+=self.term_char
        self._send(cmd)
        return self._recv(self.chunk_size)
    
    def _set_reset(self):
        # Reset Device GPIB endpoint
        self._send("++rst")        
       
    def _set_GPIB_dev_reset(self):
        # Reset Device GPIB endpoint
        self._send("*RST")        
        
    def _get_idn(self):
        return self._send_recv("*IDN ?",instrument_delay=self.instrument_delay)

    def _get_version(self):
        return self._send_recv("++ver")
    
    def _dump_internal_vars(self):
        print( "timeout"+self.timeout )
        print( "chunk_size"+ self.chunk_size ) 
        print( "values_format"+ self.values_format )
        print( "term_char"+ self.term_char )
        print( "send_end"+ self.send_end )
        print( "delay"+self.delay )
        print( "gpib_addr"+self.gpib_addr )
        print( "ip"+self.ip )
        print( "ethernet_port"+ self.ethernet_port )


    # generic error class
    class Error(Exception):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return repr(self.value)
    
    def CheckError(self):
        # check for device error
        self._send("SYST:ERR?")
        self._send("++read eoi")

        s = None

        try:
            s = self._recv(100)
        except socket.timeout:
            logging.error( "socket timeout")
            s = ""
        
        except socket.error as e:
            pass
            
        logging.error( s )
        logging.error( e )


# do some checking ...
if __name__ == "__main__":
    ls=instrument(
       "GPIB::20", 
        ip = "10.22.197.63", 
        delay = 0.1, 
        term_char = "\r",
        eos_char = "\r",
        timeout = 1,
        instrument_delay = 0,
        debug = True
        )
    ls.write("*ESE 1")
    ls.write("*SRE 32")
    ls.write("HDR 0")
    ls.write("*OPC")


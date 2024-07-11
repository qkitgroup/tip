#!/usr/bin/env python

"""
ControlByWeb X-137 DAC used as heater driver 
"""

import time
import http.client
import logging
import math
from xml.dom.minidom import parseString

from lib.tip_config import config

# debug this driver?
debug = False

def driver(name):
    #print("entering driver", flush = True)
    CBW = CBW_X_317(name, url = config[name]['url'])
    return CBW

class CBW_X_317(object):
    
    def __init__(self, name, url, **kwargs):
        self.heater_power = 0
        self.channel = 1
        self.R = 120
        self.url = url # the url string has the form "url:port", if port is omitted, port 80 (http std) is assumed
        self._setup_http_connection(self.url)

    def setup_device(self):
        pass
    
    def get_idn(self):
        return( "control by web x-317" )
        
    def get_heater_voltage(self):
        
        dev_channels  = {
            1 : "an1state",
            2 : "an2state",
            3 : "an3state",
            4 : "an4state",
            5 : "an5state",          
        }
        req  = self._http_request("/state.xml")
        data = self._read_request(req)
        dom  = self._parse_xml(data)

        voltage = dom.getElementsByTagName(dev_channels[self.channel])[0].firstChild.data
        return voltage
    
    def set_heater_voltage(self,voltage):
        """
        sv_reqests  = {
            1 : "/state.xml?noReply=1&an1State=",
            2 : "/state.xml?noReply=1&an2State=",
            3 : "/state.xml?noReply=1&an3State=",
            4 : "/state.xml?noReply=1&an4State=",
            5 : "/state.xml?noReply=1&an5State=",          
        }
        """
        sv_reqests  = {
            1 : "/state.xml?an1State=",
            2 : "/state.xml?an2State=",
            3 : "/state.xml?an3State=",
            4 : "/state.xml?an4State=",
            5 : "/state.xml?an5State=",          
        }
        formatted_voltage = "{:.5f}".format(voltage)
        req  = self._http_request(sv_reqests[self.channel]+formatted_voltage)
        return self._read_request(req)
        

    def set_heater_power(self,value):
        logging.info("set heater power: "+str(value))
        if value < 0:
            return self.set_heater_voltage(0)
            self.heater_power = 0
        else:  
            self.heater_power = value

            voltage = math.sqrt(value*self.R)
            return self.set_heater_voltage(voltage)
        
    def get_heater_channel(self):
        return self.channel

    def set_heater_channel(self,channel):
        logging.debug(f"set heater channel: {channel}")
        if channel in [1,2,3,4,5]: 
            self.channel = channel
        else:
            logging.error("CBW X-317: Only channels 1-5 are allowed.")
    
    def _setup_http_connection(self,url):
        self.conn = http.client.HTTPConnection(url)
        if debug:
            self.conn.debuglevel = 1

    def _http_request(self,request):

        self.conn.connect()  # Bugfix 23102022: for some reason, we have to reconnect at every request
        self.conn.request("GET", request)        
        res = self.conn.getresponse()
        logging.debug(f"heater http status: {res.status}  | reason: {res.reason}")

        if res.status != 200:
            raise Exception("http request failed")
        return res

    def _read_request(self, response):
        return response.read()

    def _parse_xml(self,xml_string):
        return parseString(xml_string)


    #def set_local(self):pass
    def close(self):pass

if __name__ == "__main__":
    
    ht=CBW_X_317("heater", url='10.22.197.217')
    #ht._setup_http_connection('192.168.1.2')
    #print("connected")
    #ht.conn.debuglevel = 1
    res = ht._http_request("/state.xml")
    print(ht._read_request(res))
    ht.set_heater_channel(2)
    ht.set_heater_power(0)
    #res = ht._http_request("/state.xml")
    #print(ht._read_request(res))
    #ht.set_heater_voltage(0)
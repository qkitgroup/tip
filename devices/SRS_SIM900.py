#!/usr/bin/env python

"""
SIM900 (Frame)
SIM921/SIM925(MUX)
SIM928 (Voltage Source)
Interface SIM921 resistance bridge. HR@KIT2013, 2014
"""
import sys
import visa_prologix as visa

import time
"""
exci={0:-1, 3:0, 10:1, 30:2, 100:3, 300:4, 1000:5, 3000:6, 10000:7, 30000:8}
rang={0.02:0, 0.2:1, 2:2, 20:3, 200:4, 2000:5, 20000:6, 200000:7, 2000000:8, 20000000:9}
tcon={0:-1, 0.3:0, 1:1, 3:2, 10:3, 30:4, 100:5, 300:6}

"""
class SIM900(object):
	# Fixme:port
	def __init__(self,
	             name,
	             ip="129.13.93.65",
	             gpib="GPIB::0",
	             delay = 0.2, 
	             SIM921_port=6,
	             SIM925_port=8,
                     SIM928_port=2):
		
		
		self.SIM=visa.instrument(gpib,ip=ip,delay=delay)
		self.SIM921_port = SIM921_port
		self.SIM925_port = SIM925_port
		self.SIM928_port = SIM928_port

		print "params",ip,gpib,delay,SIM921_port,SIM925_port,SIM928_port
	def error(self,str):
		print(str)
	
	def setup_device(self):
		pass
	def SIM_prolog(self,port = 0, init = False):
		try:
			# commands to mainframe
			self.SIM.write('main_esc')
			if init:
				self.SIM.write('*CLS')
				self.SIM.write('*RST')
				self.SIM.write('CEOI ON') 
				self.SIM.write('EOIX ON')
			self.SIM.write('CONN '+str(port)+', "main_esc"')
		except:
			self.error('No Connection to SIM900 MAINFRAME up to main_esc')
	
	def SIM_epilog(self):
		self.SIM.write('main_esc')
	
	def get_value_from_SIM900(self,port,cmd):
		self.SIM_prolog(port)
		val = self.SIM.ask(str(cmd))
		self.SIM_epilog()
		return val
	
	def _get_IDN(self,port):
		cmd = "*IDN?"
		return (self.get_value_from_SIM900(port,cmd)).strip()
		
		
	def get_Rval(self):
		port  = self.SIM921_port
		cmd = 'RVAL?'
		return float(self.get_value_from_SIM900(port,cmd))
	def _get_ave(self):
		# just a proxy in the moment
		return self.get_Rval()
	def _set_local(self):
		pass
	def _close(self):
		pass

	def _get_Channel(self):
		port  = self.SIM925_port
		cmd = "CHAN?"
		return int(self.get_value_from_SIM900(port,cmd))
        ########################################################
        # commands for the SIM298 isolated voltage source
        # (likely to be used as a heater ;-) )
        ########################################################
        def get_Voltage(self):
                port = self.SIM928_port
                cmd = "VOLT?"
                return float(self.get_value_from_SIM900(port,cmd))
        def set_Voltage(self,voltage):
               port = self.SIM928_port
               cmd = "VOLT "+str(voltage)+"; VOLT?"
               return float(self.get_value_from_SIM900(port,cmd))
        def set_output0(OUT_Volt): # HEATER interface
            return self.set_Voltage(OUT_Volt)
        def set_output_ON(self):
               port = self.SIM928_port
               cmd = "OPON; EXON?"
               return self.get_value_from_SIM900(port,cmd)
        def set_output_OFF(self):
               port = self.SIM928_port
               cmd = "OPOF; EXON?"
               return self.get_value_from_SIM900(port,cmd)

if __name__ == "__main__":
	# port 6 is the port to the SRS SIM921 bridge, port 8 is the SIM925 multiplexer
	SIM=SIM900("SIM900") 
	print SIM._get_IDN(8)
        print SIM._get_IDN(2)
	print SIM._get_Channel()
	print SIM.get_Rval()
	print SIM._get_ave()

	#SIM._close_connection()


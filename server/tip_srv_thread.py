#!/usr/bin/env python
# Threaded server class for tip, written by HR@KIT 2011
# purpose: create a simple tcp access for tip gui and other data 
# v0.1 initial lines, mainly taken from python doc examples. Jan. 2011

import socket
import threading
import socketserver
import time
import sys
import logging
#import numpy
try:
	import cPickle as pickle
except:
	import pickle
import json

#from string import split

DEBUG = True 
def logstr(logstring):
	if DEBUG:
		print(str(logstring))

#global wants_abort
wants_abort = False

class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):

	
	def wo(self,message):
		# write the message to the comm channel (out)
		self.wfile.write(str(message).encode())

	def set_handler(self,cmds):
		try:
			logstr(cmds)   
			if "PID".find(cmds[1]) == 0:
				if len(cmds) != 4:
					self.wo("SET/PID/Option/Value has depth 4, your command has depth %i"%len(cmds))
					return
				elif "TCTRL".find(cmds[2])==0:
					self.data.set_ctrl_Temp(float(cmds[3]))
					self.wo("1\n")		
				elif cmds[2] == "P":
					self.data.set_P(float(cmds[3]))
					self.wo("1\n")
				elif cmds[2] == "I":
					self.data.set_I(float(cmds[3]))
					self.wo("1\n")
				elif cmds[2] == "D":
					self.data.set_D(float(cmds[3]))
					self.wo("1\n")
				else:
					self.wo("Sub command after SET/PID/? not known...")
				return
			
			elif "THERMOMETER".find(cmds[1]) == 0:
				if len(cmds) != 5:
					self.wo("SET/TERM/Channel/Range/Value has depth 5, your command has depth %i"%len(cmds))
					return
				elif cmds[2] == "":
					term = self.data.bridge.Control_Channel.channel
				elif cmds[2] == ":":
					self.wo("Channel wildcard ':' not allowed in set mode.")
					return
				else:
					try:
						term = int(cmds[2])
					except ValueError:
						self.wo("Channel not recognized. Your request was "+"/".join(cmds))
						return
				try:
					if "RANGE".find(cmds[3]) == 0:
						self.data.bridge.channels[self.data.bridge.chmap[term]].set_Range(int(cmds[4]))
						self.wo("1\n")
					elif "EXCITATION".find(cmds[3]) == 0:
						self.data.bridge.channels[self.data.bridge.chmap[term]].set_Excitation(int(cmds[4]))
						self.wo("1\n")
					else:
						self.wo("Only Range and Excitation are settable in SET/THERMOMETER/X/. Set Control Temp with SET/PID/TCTRL/")
						return
				except ValueError:
					self.wo("Please specify Range or Excitation as integer value. Your request was "+"/".join(cmds))
					return

				else:
					pass
		except Exception as e:
			print ("set_handler exception... " + str(e))
			#raise e

	def get_handler(self,cmds):
		try:
			logstr(cmds)
						
			if "PID".find(cmds[1]) == 0:
				if len(cmds) == 2 or "TCTRL".find(cmds[2])==0:	self.wo(str(self.data.get_ctrl_Temp()))
				elif cmds[2] == "P":							self.wo(str(self.data.get_PID()[0]))
				elif cmds[2] == "I":							self.wo(str(self.data.get_PID()[1]))
				elif cmds[2] == "D":							self.wo(str(self.data.get_PID()[2]))
				elif "HEAT".find(cmds[2])==0:					self.wo(str(self.data.get_last_Heat()[0]))
				elif "ERROR".find(cmds[2])==0:					self.wo(str(self.data.get_last_pidE()[0]))
				elif "ALL".find(cmds[2])==0:
					print(json.dumps([T.get_Temp() for T in self.data.bridge.channels]))				
					#self.wo(pickle.dumps(self.data.get_all_pid()))
					self.wo("")
				else:											self.wo("Sub command after GET/PID/? not known...")
				return
			
			elif "THERMOMETER".find(cmds[1]) == 0:
				if cmds[2] == "":
					term = self.data.bridge.Control_Channel.channel
				elif cmds[2] == ":":
					term = -1
				else:
					try:
						term = int(cmds[2])
					except ValueError:
						self.wo(' '.join('%i'%T.channel for T in self.data.bridge.channels)) # return all available channels
						return
				try: sub_cmd = cmds[3]
				except IndexError: sub_cmd = "TEMP"  #DEFAULT
				if sub_cmd == "": sub_cmd = "TEMP"
				
				if "TEMPERATURE".find(sub_cmd) == 0:
					try:
						if "HISTORY".find(cmds[3]) == 0:
							if term == -1:	self.wo(pickle.dumps([T.get_Temp() for T in self.data.bridge.channels]))
							else:			self.wo(pickle.dumps(self.data.bridge.channels[self.data.bridge.chmap[term]].get_Temp() ))		
							return
					finally:					
						if term == -1:		self.wo(' '.join(["%f"%T.get_last_Temp() for T in self.data.bridge.channels]))
						else:				
							self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_last_Temp())
							print(self.data.bridge.channels[self.data.bridge.chmap[term]].get_last_Temp())
				elif "ALL".find(sub_cmd) == 0:
					if term == -1:			self.wo(pickle.dumps([T.get_all() for T in self.data.bridge.channels]))
					else:					self.wo(pickle.dumps(self.data.bridge.channels[self.data.bridge.chmap[term]].get_all()))
				elif "AGE".find(sub_cmd) == 0:
					try:
						if "HISTORY".find(cmds[3]) == 0:
							if term == -1:	self.wo(pickle.dumps([time.time()-T.get_timestamps() for T in self.data.bridge.channels]))
							else:			self.wo(pickle.dumps(time.time()-self.data.bridge.channels[self.data.bridge.chmap[term]].get_timestamps() ))		
							return
					finally:					
						if term == -1:		self.wo(' '.join(["%f"%T.get_age() for T in self.data.bridge.channels]))
						else:				self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_age() )
				elif "TIME".find(sub_cmd) == 0:
					try:
						if "HISTORY".find(cmds[3]) == 0:
							if term == -1:	self.wo(pickle.dumps([T.get_timestamps() for T in self.data.bridge.channels]))
							else:			self.wo(pickle.dumps(self.data.bridge.channels[self.data.bridge.chmap[term]].get_timestamps() ))		
							return
					finally:					
						if term == -1:		self.wo(' '.join(["%f"%T.get_timestamps()[-1] for T in self.data.bridge.channels]))
						else:				self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_timestamps()[-1] )
				elif "RANGE".find(sub_cmd) == 0:
					if term == -1:		self.wo(' '.join(["%i"%T.get_Range() for T in self.data.bridge.channels]))
					else:				self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_Range() )
				elif "EXCITATION".find(sub_cmd) == 0:
					if term == -1:		self.wo(' '.join(["%i"%T.get_Excitation() for T in self.data.bridge.channels]))
					else:				self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_Excitation() )
				else:
					self.wo("Sub command after GET/TEMPERATURE/? not known...")
					return

			else:
					pass
		except Exception as e:
			print ("get_handler exception..." + str(e))
			#raise e

	def checkaddress(self,ip_port):
		ip,port = ip_port
		#logging.info("Client connect from %s %s" % str(ip), str(port))
		print ("Got request from peer: %s %d "%( ip, port))
		print ("checking address ...")
		'''
		if ip=="129.13.92.191":
			print "Closing connection to",ip
			return False
		else:
			return True
		'''
		return True   
	def handle(self):
		
		if not self.checkaddress(self.request.getpeername()):
			"if the address is not valid, we close the thread"
			return
		self.data = self.server.data
		#print  "connect from host: ",self.server.socket.getpeername()
		
		
		# This while loop tackles the incoming calls per connection
		while(not self.data.get_wants_abort()):
			try:
				cmd = (self.rfile.readline()).decode().strip()
				if not cmd: break
				print(cmd)	
				cmds= cmd.upper().split("/")
				
				if "GET".find(cmds[0]) == 0: #Any abbreviation of GET would be fine (G for instance)
					self.get_handler(cmds)
				elif 'SET'.find(cmds[0]) == 0:
					self.set_handler(cmds)
				elif cmd == "0":
					#print "0 command"
					cur_thread = threading.currentThread()
					response = "%s: %s" % (cur_thread.getName(), data)
					#print "%s: %s" % (cur_thread.getName(), data)
					#response = pickle.dumps(numpy.arange(0,10),protocol=2)
					#self.request.send(response)
					self.wo(response)
					#elif cmd == "PY":
					#    exec(pycmd.remove('py '))

				elif cmd == "EXIT":
					self.wo("tip is going down\n")
					self.data.set_wants_abort()
					wants_abort = True
					break

				else:
					self.wo("Invalid syntax, either 'set' or 'get'\n")

			except KeyboardInterrupt:
				print ("handler keyboard exception")
				self.data.set_wants_abort()
				wants_abort = True
				break
			except Exception as e:
				print(str(e))
				self.data.set_wants_abort()
				wants_abort = True
				break



class THServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	def __init__(self, address, handler, data):
			self.data = data
			socketserver.TCPServer.__init__(self, address, handler)
			logging.info("Starting server")


class tip_srv(object):
	def __init__(self,DATA):
		self.data = DATA
		# Port 0 means to select an arbitrary unused port
		HOST = "0.0.0.0"
		PORT = self.data.localhost.port
		# the ThreadedTCPServer object, loaded with our request handler
		self.server = THServer((HOST, PORT), ThreadedTCPRequestHandler,self.data)
		ip, port = self.server.server_address

		# Start a thread with the server -- that thread will then start one
		# more thread for each request
		server_thread = threading.Thread(target=self.server.serve_forever)
		# Exit the server thread when the main thread terminates
		#server_thread.daemon_threads=True
		server_thread.setDaemon(True)
		server_thread.start()
		print( "Server loop running in thread: " + server_thread.getName())

	def loop(self):
		# simple 100ms event loop
		while(True):
			# print self.server.socket.getpeername()
			#print wants_abort
			try:
				if self.data.get_wants_abort():
					print("\n############################ Received TIP server shutdown signal ############################")
					self.server.shutdown()
					break
					return False
				time.sleep(0.1)

			except KeyboardInterrupt:
				self.data.set_wants_abort()
				print ("\n###### Keybord Interrupt: Shutting down TIP ...")
				break


if __name__ == "__main__":
	tipserv = tip_srv("DATA")
	tipserv.loop()

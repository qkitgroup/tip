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

#from string import split

DEBUG = False 
def logstr(logstring):
	if DEBUG:
		print(str(logstring))

#global wants_abort
wants_abort = False

class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
#    def __init__(self,data):
#   SocketServer.StreamRequestHandler.__init__(self)
#   self.data = data
  
	def set_handler(self,cmds):
		try:
			logstr(cmds)   
			if "PID".find(cmds[1]) == 0:
				if len(cmds) != 4:
					self.wfile.write("SET/PID/Option/Value has depth 4, your command has depth %i"%len(cmds))
					return
				elif "TCTRL".find(cmds[2])==0:
					self.data.set_ctrl_Temp(float(cmds[3]))
					self.wfile.write("1\n")		
				elif cmds[2] == "P":
					self.data.set_P(float(cmds[3]))
					self.wfile.write("1\n")
				elif cmds[2] == "I":
					self.data.set_I(float(cmds[3]))
					self.wfile.write("1\n")
				elif cmds[2] == "D":
					self.data.set_D(float(cmds[3]))
					self.wfile.write("1\n")
				else:
					self.wfile.write("Sub command after SET/PID/? not known...")
				return
			
			elif "THERMOMETER".find(cmds[1]) == 0:
				if len(cmds) != 5:
					self.wfile.write("SET/TERM/Channel/Range/Value has depth 5, your command has depth %i"%len(cmds))
					return
				elif cmds[2] == "":
					term = self.data.bridge.Control_Channel.channel
				elif cmds[2] == ":":
					self.wfile.write("Channel wildcard ':' not allowed in set mode.")
					return
				else:
					try:
						term = int(cmds[2])
					except ValueError:
						self.wfile.write("Channel not recognized. Your request was "+"/".join(cmds))
						return
				try:
					if "RANGE".find(cmds[3]) == 0:
						self.data.bridge.channels[self.data.bridge.chmap[term]].set_Range(int(cmds[4]))
						self.wfile.write("1\n")
					elif "EXCITATION".find(cmds[3]) == 0:
						self.data.bridge.channels[self.data.bridge.chmap[term]].set_Excitation(int(cmds[4]))
						self.wfile.write("1\n")
					else:
						self.wfile.write("Only Range and Excitation are settable in SET/THERMOMETER/X/. Set Control Temp with SET/PID/TCTRL/")
						return
				except ValueError:
					self.wfile.write("Please specify Range or Excitation as integer value. Your request was "+"/".join(cmds))
					return

				else:
					pass
		except:
			print ("set_handler exception...")
			raise

	def get_handler(self,cmds):
		try:
			logstr(cmds)   
			
			if "PID".find(cmds[1]) == 0:
				if len(cmds == 2) or "TCTRL".find(cmds[2])==0:	self.wfile.write(str(self.data.get_ctrl_Temp()))
				elif cmds[2] == "P":							self.wfile.write(str(self.data.get_PID()[0]))
				elif cmds[2] == "I":							self.wfile.write(str(self.data.get_PID()[1]))
				elif cmds[2] == "D":							self.wfile.write(str(self.data.get_PID()[2]))
				elif "HEAT".find(cmds[2])==0:					self.wfile.write(str(self.data.get_last_Heat()[0]))
				elif "ERROR".find(cmds[2])==0:					self.wfile.write(str(self.data.get_last_pidE()[0]))
				elif "ALL".find(cmds[2])==0:					self.wfile.write(pickle.dumps(self.data.get_all_pid()))
				else:											self.wfile.write("Sub command after GET/PID/? not known...")
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
						self.wfile.write(' '.join('%i'%T.channel for T in self.data.bridge.channels)) # return all available channels
						return
				try: sub_cmd = cmds[3]
				except IndexError: sub_cmd = "TEMP"  #DEFAULT
				if sub_cmd == "": sub_cmd = "TEMP"
				
				if "TEMPERATURE".find(sub_cmd) == 0:
					try:
						if "HISTORY".find(cmds[4]) == 0:
							if term == -1:	self.wfile.write(pickle.dumps([T.get_Temp() for T in self.data.bridge.channels]))
							else:			self.wfile.write(pickle.dumps(self.data.bridge.channels[self.data.bridge.chmap[term]].get_Temp() ))		
							return
					finally:					
						if term == -1:		self.wfile.write(' '.join(["%f"%T.get_last_Temp() for T in self.data.bridge.channels]))
						else:				self.wfile.write(self.data.bridge.channels[self.data.bridge.chmap[term]].get_last_Temp() )
				elif "ALL".find(sub_cmd) == 0:
					if term == -1:			self.wfile.write(pickle.dumps([T.get_all() for T in self.data.bridge.channels]))
					else:					self.wfile.write(pickle.dumps(self.data.bridge.channels[self.data.bridge.chmap[term]].get_all()))
				elif "AGE".find(sub_cmd) == 0:
					try:
						if "HISTORY".find(cmds[4]) == 0:
							if term == -1:	self.wfile.write(pickle.dumps([time.time()-T.get_timestamps() for T in self.data.bridge.channels]))
							else:			self.wfile.write(pickle.dumps(time.time()-self.data.bridge.channels[self.data.bridge.chmap[term]].get_timestamps() ))		
							return
					finally:					
						if term == -1:		self.wfile.write(' '.join(["%f"%T.get_age() for T in self.data.bridge.channels]))
						else:				self.wfile.write(self.data.bridge.channels[self.data.bridge.chmap[term]].get_age() )
				elif "TIME".find(sub_cmd) == 0:
					try:
						if "HISTORY".find(cmds[4]) == 0:
							if term == -1:	self.wfile.write(pickle.dumps([T.get_timestamps() for T in self.data.bridge.channels]))
							else:			self.wfile.write(pickle.dumps(self.data.bridge.channels[self.data.bridge.chmap[term]].get_timestamps() ))		
							return
					finally:					
						if term == -1:		self.wfile.write(' '.join(["%f"%T.get_timestamps()[-1] for T in self.data.bridge.channels]))
						else:				self.wfile.write(self.data.bridge.channels[self.data.bridge.chmap[term]].get_timestamps()[-1] )
				elif "RANGE".find(sub_cmd) == 0:
					if term == -1:		self.wfile.write(' '.join(["%i"%T.get_Range() for T in self.data.bridge.channels]))
					else:				self.wfile.write(self.data.bridge.channels[self.data.bridge.chmap[term]].get_Range() )
				elif "EXCITATION".find(sub_cmd) == 0:
					if term == -1:		self.wfile.write(' '.join(["%i"%T.get_Excitation() for T in self.data.bridge.channels]))
					else:				self.wfile.write(self.data.bridge.channels[self.data.bridge.chmap[term]].get_Excitation() )
				else:
					self.wfile.write("Sub command after GET/TEMPERATURE/? not known...")
					return

			else:
					pass
		except:
			print ("get_handler exception...")
			raise

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
		return True   #Jochen
	def handle(self):
		
		if not self.checkaddress(self.request.getpeername()):
			"if the address is not valid, we close the thread"
			return
		self.data = self.server.data
		#print  "connect from host: ",self.server.socket.getpeername()
		
		
		# This while loop tackles the incoming calls per connection
		while(True):
			try:
				cmd = self.rfile.readline().strip()
				if not cmd: break
								
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
					self.wfile.write(response)
					#elif cmd == "PY":
					#    exec(pycmd.remove('py '))

				elif cmd == "EXIT":
					self.wfile.write("tip is going down\n")
					self.data.set_wants_abort()
					wants_abort = True
					break

				else:
					self.wfile.write("Invalid syntax, either 'set' or 'get'\n")

			except KeyboardInterrupt:
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
		#HOST, PORT = "localhost", 9999
		#HOST, PORT = "pi-us27", 9999
		#HOST = self.data.localhost.name # we open now to both local and remote
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
		# server.shutdown()

	def loop(self):
		# simple 100ms event loop
		while(True):
			# print self.server.socket.getpeername()
			#print wants_abort
			try:
				if self.data.get_wants_abort():
					self.server.shutdown()
					print("TIP server shutdown ############################")
					break
					#time.sleep(0.1)
					return False
				time.sleep(0.1)

			except KeyboardInterrupt:
				self.data.set_wants_abort()
				print ("Shutting down...")


if __name__ == "__main__":
	tipserv = tip_srv("DATA")
	tipserv.loop()

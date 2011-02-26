#!/usr/bin/env python

import socket
import sys
import numpy
import pickle
import time
class remote_client(object):
	def setup(self):
		HOST, PORT = "localhost", 9999

		# Create a socket (SOCK_STREAM means a TCP socket)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# Connect to server and send data
		self.sock.connect((HOST, PORT))

	def send(self):
		#sdata = " ".join(sys.argv[1:])
		sdata = "set T 0.05 "	
		self.sock.send(sdata + "\n")
	def recv(self):
		# Receive data from the server and shut down
		rdata = self.sock.recv(8192)
		#rdata = self.sock.recv(1024)
		
		#string = "" 
		#while len(rdata):
  		#	string = string + rdata
  		#	rdata = self.sock.recv(1024)

		string = rdata
		#print "Sent:     %s" % sdata
		#print "Received s: %s" % numpy.array(received).tostring()
		#print len(string),
		#arr= pickle.loads(string)
		#print arr
		print string
	def close(self):
		self.sock.close()

if __name__=="__main__":
	rc=remote_client()
	rc.setup()
	t=time.time()
	for i in numpy.arange(3):
		rc.send()
		rc.recv()
		#time.sleep(1)
	print time.time()-t
	rc.close()


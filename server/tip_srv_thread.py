#!/usr/bin/env python
# Threaded server class for tip, written by HR@KIT 2011
# purpose: create a simple tcp access for tip gui and other data 
# v0.1 initial lines, mainly taken from python doc examples. Jan. 2011

import socket
import threading
import SocketServer
import time
import sys
import logging
#import numpy
try:
    import cPickle as pickle
except:
    import pickle

from string import split

DEBUG = False 
def logstr(logstring):
    if DEBUG:
        print(str(logstring))

#global wants_abort
wants_abort = False

class ThreadedTCPRequestHandler(SocketServer.StreamRequestHandler):
#    def __init__(self,data):
#	SocketServer.StreamRequestHandler.__init__(self)
#	self.data = data

    def set_handler(self,cmds):
        try:
            print cmds	
            cmd = cmds.pop(0)
            if cmd == 'T' or cmd == 'TCTRL':
                T=float(cmds.pop(0))
                self.wfile.write("1\n")
                self.data.set_ctrl_Temp(T)

            elif cmd == 'PID':
                PID = float(cmds.pop(0)),float(cmds.pop(0)),float(cmds.pop(0))
                print PID
                self.data.set_PID(PID)
                self.wfile.write("1\n")
                
            elif cmd == 'BRANGE':
                BRANGE = float(cmds.pop(0))
                print BRANGE
                self.data.bridge.set_Range(BRANGE)
                self.wfile.write("1\n")
            elif cmd == 'BRIDGE':
                sub_cmd = cmds.pop(0)
                if   sub_cmd == 'RANGE':
                    self.wfile.write(str(self.data.bridge.set_Range(int(cmds.pop(0)))))
                elif sub_cmd == 'RAN':
                    self.wfile.write(str(self.data.bridge.set_Range(int(cmds.pop(0)))))
                elif sub_cmd == 'EXC':
                    self.wfile.write(str(self.data.bridge.set_Excitation(int(cmds.pop(0)))))
                elif sub_cmd == 'EXCITATION':
                    self.wfile.write(str(self.data.bridge.set_Excitation(int(cmds.pop(0)))))
                elif sub_cmd == 'CHA':
                    self.wfile.write(str(self.data.bridge.set_Channel(int(cmds.pop(0)))))
                elif sub_cmd == 'CHANNEL':
                    self.wfile.write(str(self.data.bridge.set_Channel(int(cmds.pop(0)))))
                else:
                    self.wfile.write("BRIDGE: Syntax error")
            
            else:
                pass
        except:
            print "set_handler exception..."
            raise

    def get_handler(self,cmds):
        try:
            logstr(cmds)          
            cmd = cmds.pop(0)
            # only send T
            if cmd == 'T':
                self.wfile.write(str(self.data.get_last_Temp()))
            elif cmd == 'TCTRL':
                self.wfile.write(str(self.data.get_ctrl_Temp()))
            elif cmd == 'PID':
                self.wfile.write(str(self.data.get_PID()[0])+' '+str(self.data.get_PID()[1])+' '+str(self.data.get_PID()[2]))
            elif cmd == 'HEAT':
                self.wfile.write(str(self.data.get_last_Heat()))
            elif cmd == 'PIDE':
                self.wfile.write(str(self.data.get_last_pidE()))
            elif cmd == 'RES':
                self.wfile.write(str(self.data.get_last_Res()))
            elif cmd == 'BRANGE':
                self.wfile.write(str(self.data.bridge.get_Range()))
            elif cmd == 'BRIDGE':
                sub_cmd = cmds.pop(0)
                if   sub_cmd == 'RANGE':
                    self.wfile.write(str(self.data.bridge.get_Range()))
                elif sub_cmd == 'RAN':
                    self.wfile.write(str(self.data.bridge.get_Range()))
                elif sub_cmd == 'EXC':
                    self.wfile.write(str(self.data.bridge.get_Excitation()))
                elif sub_cmd == 'EXCITATION':
                    self.wfile.write(str(self.data.bridge.get_Excitation()))
                elif sub_cmd == 'CHA':
                    self.wfile.write(str(self.data.bridge.get_Channel()))
                elif sub_cmd == 'CHANNEL':
                    self.wfile.write(str(self.data.bridge.get_Channel()))
                else:
                    self.wfile.write("BRIDGE: Syntax error")
            # send active state
            elif cmd == 'S':	
                self.wfile.write(str(T))
            # send configuration object
            elif cmd == 'CFG':
                CFG = ""
                self.wfile.write(str(CFG))
            else:
                    pass
        except:
                raise

    def checkaddress(self,(ip,port)):
        #logging.info("Client connect from %s %s" % str(ip), str(port))
        print ip, port

    def handle(self):
        self.checkaddress(self.request.getpeername())
        self.data = self.server.data

        
            
        # This while loop tackles the incoming calls per connection
        while(True):
            cmd = self.rfile.readline().strip()
            # connection closed, thread dies
            if not cmd: break
            # get/set
            pycmd= cmd
            cmds= cmd.upper().split()
            cmd=cmds.pop(0)
            if   cmd == 'GET':
                self.get_handler(cmds)
            elif cmd == 'SET':
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

class THServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	def __init__(self, address, handler, data):
			self.data = data
			SocketServer.TCPServer.__init__(self, address, handler)
			logging.info("Starting server")


class tip_srv(object):
    def __init__(self,DATA):
        self.data = DATA
        # Port 0 means to select an arbitrary unused port
        #HOST, PORT = "localhost", 9999
        HOST, PORT = "pi-us27", 9999
        
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
        # simple 10ms event loop
        while(True):
            #print wants_abort
            if self.data.get_wants_abort():
                self.server.shutdown()
                print("TIP server shutdown ############################")
                break
            time.sleep(0.1)


if __name__ == "__main__":
    tipserv = tip_srv("DATA")
    tipserv.loop()

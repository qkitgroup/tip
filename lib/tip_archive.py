from traits.api import *
from traitsui.api import View, Item
from scipy import *
from threading import Thread
from time import sleep
import numpy
import h5py
import socket

from tip_log_backend import H5_LOGFILE

    
UpdateInterval = 2
DEBUG = True

REMOTEHOST = 'pi-us71'
REMOTEPORT = 9999

#--------------------------------------------------------------


class remote_client(object):
    def __init__(self,host = REMOTEHOST, port = REMOTEPORT):
        self.setup(host,port)
        
    def setup(self,HOST,PORT):
        try:
            # Create a socket (SOCK_STREAM means a TCP socket)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Connect to server and send data
            self.sock.connect((HOST, PORT))
            logstr("connected to %s port %d\n"%(HOST,PORT))
        except:
            raise

    def send(self,send_cmd):
        self.sock.send(send_cmd + "\n")
        
    def recv(self):
        # Receive data from the server and shut down
        rdata = self.sock.recv(8192)
        string = rdata
        #arr= pickle.loads(string)
        #logstr(string)
        return string
    
    def close(self):
        self.sock.close()
        
        
#----------------------------------------------------------------


class DataAcquisitionThread(Thread):

    wants_abort = False
    
    logfile = H5_LOGFILE('log.h5')
        
    T_sink = logfile.new_sink('Temperature')
    pidE_sink = logfile.new_sink('PID_Error')
    Heat_sink = logfile.new_sink('Heat')
    Tctrl_sink = logfile.new_sink('Tctrl')
    R_sink = logfile.new_sink('Res')
        
    def setup_acquire_from_remote(self):
        self.rc=remote_client()
    def acquire_from_remote(self,cmd):
        self.rc.send("get "+cmd)
        return self.rc.recv()

    def update_remote(self,cmd):
        self.rc.send(str("set "+cmd))

    def stop_remote(self):
        self.rc.send("EXIT\n")
        self.rc.close()
    def process(self, image):
        """ Spawns the processing job.
        """
        try:
            if self.processing_job.isAlive():
                self.display("Processing to slow")
                return
        except AttributeError:
            pass
        self.processing_job.start()

    def run(self):
        """ Runs the acquisition loop.
        """
        
        #self.logfile = H5_LOGFILE('log.h5')
        #
        #self.T_sink = self.logfile.new_sink('Temperature')
        #
        #self.pidE_sink = logfile.new_sink('PID_Error')
        #self.Heat_sink = logfile.new_sink('Heat')
        #self.Tctrl_sink = logfile.new_sink('Tctrl')
        #self.R_sink = logfile.new_sink('Res')
        
        self.setup_acquire_from_remote()

        self.display('Start')
                
        while not self.wants_abort:
            # get state
            T=float(self.acquire_from_remote("T"))
            Heat=float(self.acquire_from_remote("HEAT"))
            pidE=float(self.acquire_from_remote("PIDE"))
            Tctrl=float(self.acquire_from_remote("TCTRL"))
            R=float(self.acquire_from_remote("RES"))
            
            self.logfile.append(T_sink,T)
            self.logfile.append(Heat_sink,Heat)
            self.logfile.append(pidE_sink,pidE)
            self.logfile.append(Tctrl_sink,Tctrl)
            self.logfile.append(R_sink,R)

            sleep(UpdateInterval)
            
        #self.stop_remote()
        self.display('Connection stopped')
        

class Control(HasTraits):
    
    start_stop_acquisition = Button("Start/Stop")
    acquisition_thread = Instance(DataAcquisitionThread)
    view = View(Item('start_stop_acquisition'))
    
    def _start_stop_acquisition_fired(self):
        """ Callback of the "start stop acquisition" button. This starts
            the acquisition thread, or kills it/
        """
        if self.acquisition_thread and self.acquisition_thread.isAlive():
            self.acquisition_thread.wants_abort = True
        else:
            # connect the function calls
            self.acquisition_thread = DataAcquisitionThread()
            self.acquisition_thread.display = self.add_line

            #self.acquisition_thread.state = self.state
            
            #self.acquisition_thread.update_plots = self.update_plots
    
            self.acquisition_thread.start()

    def add_line(self, string):
        """ Adds a line to the textbox display.
        """
        self.results_string = (string + "\n" + self.results_string)[0:1000]
 
        
                      
if __name__ == '__main__':
    Control().configure_traits()       
#----------------------------------------------------------------------------
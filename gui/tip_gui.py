#!/usr/bin/env python
# -*- coding: utf-8 -*-
#tip gui version 0.1 written by HR@KIT 2011

# traids stuff
from traits.api import *
from traitsui.api import View, Item, Group, \
        VSplit,HSplit, Handler,VGroup,HGroup
from traitsui.menu import NoButtons

from scipy import *
from threading import Thread
from time import sleep
import numpy

from chaco.api import Plot, ArrayPlotData
from chaco.tools.api import PanTool, ZoomTool, DragZoom
from enable.component_editor import ComponentEditor
from chaco.chaco_plot_editor import ChacoPlotItem

import socket
try:
    import cPickle as pickle
except:
    import pickle

UpdateInterval = 2
DEBUG = True

REMOTEHOST = 'pi-us71'
REMOTEPORT = 9999

def logstr(logstring):
    if DEBUG:
        print(str(logstring))
    
class Error(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class Bridge(HasTraits):
    """ Object to display on the conifiguration
    """
    Bridge = Str("AVS 47",label="Resistance Bridge")
    #Delay = Float()
    Channel = Enum("0","1","2","3","4","5","6","7",)
    Excitation = Enum("NONE", "3uV", "10uV", "30uV", "100uV", "300uV", "1mV", "3mV")
    Range = Enum("2R","20R","200R","2K","20K","200K","2M")
    AutoRange = Bool()
    Update = Button("Update")
    
    view = View(Group(
        Item('Bridge',style='readonly'),
        #Item('Delay',label="Delay"),
        Item('Channel',label="Channel"),
        Item('Range',label="Range"),
        Item('Excitation',label="Excitation"),
        Item('AutoRange',label="Autorange")
	),
        Item("Update",label="Update all")
        )

    def _Update_fired(self):
        """ Callback of the update button.
        """
        range_map_r= {0:'NONE', 1:'2R', 2:'20R', 3:'200R', 4:'2K', 5:'20K', 6:'200K', 7:'2M'}
        exc_map_r=  {0:"NONE", 1:"3uV", 2:"10uV", 3:"30uV", 4:"100uV", 5:"300uV", 6:"1mV", 7:"3mV"}
        channel_map_r= {0:"0", 1:"1", 2:"2", 3:"3", 4:"4", 5:"5", 6:"6", 7:"7"}
        
        rc = remote_client()
        rc.send("get Bridge Range")
        self.Range=range_map_r.get(int(rc.recv()))
        
        rc.send("get Bridge excitation")
        self.Excitation=exc_map_r.get(int(rc.recv()))
        
        rc.send("get Bridge channel")
        self.Channel = channel_map_r.get(int(rc.recv()))
        rc.close()
        
    def _AutoRange_changed(self):
        #range_map= {'NONE':0, '2R':1, '20R':2, '200R':3, '2K':4, '20K':5, '200K':6, '2M':7}
        rc = remote_client()  
        #rc.send("set BRange "+str(range_map.get(self.Range)))
        if AutoRange:
            rc.send("set Bridge Range "+str(10))
        else:
            # for now AutoRange is not really implemented ;-)
            rc.send("set Bridge Range "+str(10))
        if not rc.recv().strip() == '1':
            raise Error("communication error")
        rc.close()
        
    def _Range_changed(self):
        range_map= {'NONE':0, '2R':1, '20R':2, '200R':3, '2K':4, '20K':5, '200K':6, '2M':7}
        rc = remote_client()  
        #rc.send("set BRange "+str(range_map.get(self.Range)))
        rc.send("set Bridge Range "+str(range_map.get(self.Range)))
        if not rc.recv().strip() == '1':
            raise Error("communication error")
        rc.close()

    def _Excitation_changed(self):
        exc_map= {"NONE":0, "3uV":1, "10uV":2, "30uV":3, "100uV":4, "300uV":5, "1mV":6, "3mV":7}
        rc = remote_client()  
        rc.send("set Bridge excitation "+str(exc_map.get(self.Excitation)))
        if not rc.recv().strip() == '1':
            raise Error("communication error")
        rc.close()

    def _Channel_changed(self):
        channel_map= {"0":0, "1":1, "2":2, "3":3, "4":4, "5":5, "6":6, "7":7}
        rc = remote_client()  
        rc.send("set Bridge channel "+str(channel_map.get(self.Channel)))
        if not rc.recv().strip() == '1':
            raise Error("communication error")
        rc.close()
    
class State(HasTraits):
    T = Float(1)
    Tctrl_display = Float(0.00,desc="Target temperature for control")
    R = Float(1000000.0)
    H = Float(0)

    pid_Update = Button("pid_Update")
    
    Tctrl = Float(0.00,auto_set=False, enter_set=True,desc="Target temperature for control")
    P =    Float(0.05,auto_set=False, enter_set=True,desc="proportional gain for pid")
    I = Float(0.01,auto_set=False, enter_set=True,desc="integral gain for pid")
    D = Float(0,auto_set=False, enter_set=True,desc="differential gain for pid")
    P_disp = Float(0.00,desc="set P parameter")
    I_disp = Float(0.00,desc="set I parameter")
    D_disp = Float(0.00,desc="set D parameter")

    
    view = View(Group(Group(
        HGroup( Item(name='T',format_str="%.5f K",style='readonly'),
                Item(name='R',format_str="%.1f Ohm",style='readonly'),
                Item(name='H',format_str="%.4f uW",style='readonly')),
        HGroup( Item(name='Tctrl_display',label='set T',format_str="%.5f K",style='readonly'),
                Item(name="Tctrl",label='new T (K)',format_str="%.5f")),
                label="Temperature",show_border=True),
        Group(
        HGroup( Item(name='P_disp',label='P',format_str="%.5f",style='readonly'),
                Item(name='I_disp',label='I',format_str="%.5f",style='readonly'),
                Item(name='D_disp',label='D',format_str="%.5f",style='readonly'),
                Item(name='pid_Update',label='Update',show_label=False)),
        HGroup( Item('P'), Item('I'), Item('D')),label="PID parameters",show_border=True
              )
        ))

    def _update_fired(self):
        rc = remote_client()    
        rc.send("set T "+str(self.Tctrl))
        if not int(rc.recv().strip()) == 1:
            raise Error("communication error")
        rc.send("set PID %.3f %.3f %.3f"% (self.P,self.I,self.D))
        if not int(rc.recv().strip()) == 1:
            raise Error("communication error")
        rc.close()

    def _pid_Update_fired(self):

        rc = remote_client()
        
        rc.send("GET PID")
        pid_str=rc.recv().split()
        rc.close()
        self.P = float(pid_str[0])
        self.I = float(pid_str[1])
        self.D = float(pid_str[2])
        self.P_disp = self.P
        self.I_disp = self.I
        self.D_disp = self.D
        
    def _Tctrl_changed(self):
        rc = remote_client()    
        rc.send("set T "+str(self.Tctrl))
        if not int(rc.recv().strip()) == 1:
            raise Error("communication error")
        rc.close()

    def _P_changed(self):
        self.update_PID()
    def _I_changed(self):
        self.update_PID()
    def _D_changed(self):
        self.update_PID()

        
    def update_PID(self):
        rc = remote_client()
        rc.send("set PID %.5f %.5f %.5f"% (self.P,self.I,self.D))
        if not int(rc.recv().strip()) == 1:
            raise Error("communication error")
        rc.close()
 
        
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
        
class AcquisitionThread(Thread):
    """ Acquisition loop. This is the worker thread that retrieves info ...
    """
    wants_abort = False
    
    
    
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
        self.T_arr =numpy.zeros(100)
        self.pidE_arr=numpy.zeros(100)
        self.Heat_arr = numpy.zeros(100)
        self.time = numpy.arange(100)
        self.setup_acquire_from_remote()

        self.T_arr[:]=float(self.acquire_from_remote("T"))*1000
        self.Heat_arr[:]=float(self.acquire_from_remote("HEAT"))*1e6
        self.pidE_arr[:]=float(self.acquire_from_remote("PIDE"))*1e6


        self.display('Start')
                
        while not self.wants_abort:
            # get state
            T=float(self.acquire_from_remote("T"))
            Heat=float(self.acquire_from_remote("HEAT"))
            pidE=float(self.acquire_from_remote("PIDE"))
            Tctrl=float(self.acquire_from_remote("TCTRL"))
            R=float(self.acquire_from_remote("RES"))

            self.state.T = float(T)
            self.state.R = float(R)
            self.state.H = float(Heat)*1e6
            self.state.Tctrl_display = float(Tctrl)
            self.T_arr = numpy.delete(numpy.append(self.T_arr,T*1e3),0)
            self.pidE_arr = numpy.delete(numpy.append(self.pidE_arr,pidE*1e6),0)
            self.Heat_arr = numpy.delete(numpy.append(self.Heat_arr,Heat*1e6),0)
            self.update_plots(self.time,self.T_arr,self.Heat_arr,self.pidE_arr)
            sleep(UpdateInterval)
            
        #self.stop_remote()
        self.display('Connection stopped')


# The GUI elements
#------------------

class ControlPanel(HasTraits):
    """ This object is the core of the traitsUI interface. Its view is
        the right panel of the application, and it hosts the method for
        interaction between the objects and the GUI.
    """
    Bridge = Instance(Bridge,())
    
    state = Instance(State,())
    
    time = Array
    T_arr = Array
    Heat_arr = Array
    pidE_arr = Array
    
    start_stop_acquisition = Button("Start/Stop")
    results_string =  String()
    acquisition_thread = Instance(AcquisitionThread)
    view = View(
        Group(HSplit(
            VSplit(
                ChacoPlotItem("time", "T_arr",
                               show_label=False,
                               resizable=True,
                               x_label="time / s",
                               y_label="T / mK",
                               #x_bounds=(0,100),
                               x_auto=True,
                               #y_bounds=(0,1),
                               y_auto=True,
                               color="blue",
                               bgcolor="white",
                               border_visible=True,
                               border_width=2,
                               title='Temperature / mK',
                               padding_bg_color="lightgrey"),
                ChacoPlotItem("time", "Heat_arr",
                               show_label=False,
                               resizable=True,
                               x_label="time / s",
                               y_label="Heat / uW",
                               x_auto=True,
                               y_auto=True,
                               color="blue",
                               bgcolor="white",
                               border_visible=True,
                               border_width=2,
                               title='Heat / uW',
                               padding_bg_color="lightgrey"),
                ChacoPlotItem("time", "pidE_arr",
                               show_label=False,
                               resizable=True,
                               x_label="time / s",
                               y_label="Error / uK",
                               x_auto=True,
                               y_auto=True,
                               color="blue",
                               bgcolor="white",
                               border_visible=True,
                               border_width=2,
                               title='PID Error / uK',
                               padding_bg_color="lightgrey")),
            VSplit(
            Group(Item('state',style='custom',show_label=False,label='State')),
            
            Group(
                    Group(
                    Item('start_stop_acquisition', show_label=False ),
                    Item('results_string',show_label=False,springy=True, style='custom' ),
                    label="Control", dock='tab',
                    ),
                    Group(
                        Group(
                        Item('Bridge',style='custom',show_label=False),
                        show_border=True,label='Bridge',
                        ), label='Bridge', dock="tab",
                    ),
                    layout='tabbed'
                ),
            ),
        )))

    def _start_stop_acquisition_fired(self):
        """ Callback of the "start stop acquisition" button. This starts
            the acquisition thread, or kills it/
        """
        if self.acquisition_thread and self.acquisition_thread.isAlive():
            self.acquisition_thread.wants_abort = True
        else:
            # connect the function calls
            self.acquisition_thread = AcquisitionThread()
            self.acquisition_thread.display = self.add_line

            #self.acquisition_thread.time = self.data.time
            #self.acquisition_thread.T_arr = self.data.T_arr
            #self.acquisition_thread.pidE_arr = self.data.pidE_arr
            #self.acquisition_thread.Heat_arr = self.data.Heat_arr
            self.acquisition_thread.state = self.state
            
            self.acquisition_thread.update_plots = self.update_plots
    
            self.acquisition_thread.start()

    def add_line(self, string):
        """ Adds a line to the textbox display.
        """
        self.results_string = (string + "\n" + self.results_string)[0:1000]
        
    def update_plots(self,xdata,ydata0,ydata1,ydata2):
        
        self.time = xdata
        self.T_arr = ydata0
        self.Heat_arr = ydata1
        self.pidE_arr = ydata2
        
    def _time_default(self): 
        return numpy.arange(100)
        
    def _T_arr_default(self): 
        return numpy.zeros(100)
        
    def _Heat_arr_default(self): 
        return numpy.zeros(100)
        
    def _pidE_arr_default(self): 
        return numpy.zeros(100)
      


class MainWindowHandler(Handler):
    def close(self, info, is_OK):
        if ( info.object.panel.acquisition_thread 
             and info.object.panel.acquisition_thread.isAlive() ):
            info.object.panel.acquisition_thread.wants_abort = True
            while info.object.panel.acquisition_thread.isAlive():
                sleep(0.1)
            wx.Yield()
        return True


class MainWindow(HasTraits):
    """ The main window, here go the instructions to create and destroy
        the application.
    """
    panel = Instance(ControlPanel)
    
    def _panel_default(self):
 	return ControlPanel()
    
    view = View(HSplit( 
                        Item('panel', style="custom"),
                        show_labels=False, 
                       ),
                resizable=True, 
                height=0.8, width=0.8,
                handler=MainWindowHandler(),
                title='TIP Temperature Information Program (GUI frontend)',
                buttons=NoButtons
                )
                

if __name__ == '__main__':
    MainWindow().configure_traits()

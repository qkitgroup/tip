# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 21:59:44 2015

@author: hrotzing
"""
from threading import Thread
from time import sleep

from lib.tip_zmq_client_lib import context, get_config, get_device, get_param, set_param, set_exit


from PyQt5.QtCore import  QObject, pyqtSignal

class DATA(object):
    #REMOTEHOST = "localhost"
    #REMOTEPORT = 9999
    UpdateInterval = 2
    DEBUG = False
    wants_abort = True
    Thermometer = None


def logstr(logstring):
    print(str(logstring))
    
class Error(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

        
class AcquisitionThread(Thread,QObject):
    """ Acquisition loop. This is the worker thread that retrieves info ...
    """
    T_sig   = pyqtSignal(float)
    H_sig   = pyqtSignal(float)
    E_sig   = pyqtSignal(float)
    R_sig   = pyqtSignal(float)
    C_T_sig = pyqtSignal(float)
    P_sig   = pyqtSignal(float)
    I_sig   = pyqtSignal(float)
    D_sig   = pyqtSignal(float)
    Int_sig = pyqtSignal(float)
    DR_sig   = pyqtSignal(float)
    DE_sig   = pyqtSignal(float)
    def __init__(self,DATA):
        Thread.__init__(self)
        QObject.__init__(self)
        DATA.wants_abort = False
        self.data = DATA
    """
    def acquire_from_remote(self,device,param): 
        return (get_param(device,param))

    def update_remote(self,device,cmd):
        return (set_param(device,param))
    """
    def stop_remote(self):
        return (set_exit())
        
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
    def display(self,message):
        print (message)

    def run(self):
        """ Runs the acquisition loop.
        """
        R=0
        Heat =0

        self.display('Start')
                
        while not self.data.wants_abort:
            # get state
            
            thermometer_data = get_device(self.data.thermometer)
            T        = float(thermometer_data["temperature"])
            Heat     = float(thermometer_data["heating_power"])
            pidE     = float(thermometer_data["control_error"])
            R        = float(thermometer_data["resistance"])
            C_T      = float(thermometer_data["control_temperature"])
            P        = float(thermometer_data["control_p"])
            I        = float(thermometer_data["control_i"])
            D        = float(thermometer_data["control_d"])

            DR       = int(thermometer_data["device_range"])
            DE       = int(thermometer_data["device_excitation"])
            interval = float(thermometer_data['interval'])

            self.T_sig.emit(T)
            self.H_sig.emit(Heat)
            self.E_sig.emit(pidE)
            self.R_sig.emit(R)
            self.C_T_sig.emit(C_T)
            self.P_sig.emit(P)
            self.I_sig.emit(I)
            self.D_sig.emit(D)
            self.DR_sig.emit(DR)
            self.DE_sig.emit(DE)
            self.Int_sig.emit(interval)

            #sleep(self.data.UpdateInterval)
            
            # make sure the gui stays reponsive, 3 s max delay. 
            if interval > 3: 
                interval = 3
            sleep(interval)
            
            
        self.display('Connection stopped')
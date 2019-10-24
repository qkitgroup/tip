# tip regulation gui / HR@KIT 2011 - 2019
import sys

# make it pyqt5 only ...
#from PyQt4.QtCore import *
#from PyQt4.QtGui import *
from PyQt5.QtCore import * #Qt, QObject
from PyQt5.QtWidgets import * # QApplication


from time import sleep

from gui.tip_gui_lib import DATA, AcquisitionThread #,  remote_client
from gui.tip_gui_cover import Ui_MainWindow

import argparse
import configparser
import numpy


from lib.tip_zmq_client_lib import setup_connection, get_config, get_param, set_param, set_exit


class MainWindow(QMainWindow, Ui_MainWindow):

    # custom slot

    def myquit(self):
        exit()

    def __init__(self,data):
        self.data = data

        QMainWindow.__init__(self)
        # set up User Interface (widgets, layout...)
        self.setupUi(self)
        #self.menubar.setNativeMenuBar(False)
        self._setup_signal_slots()
        self._setup_views()

        setup_connection("tcp://localhost:5000")

        self.acquisition_thread =False
        
        self.Temps =numpy.empty(100)
        self.Temps.fill(numpy.nan)
        self.Errors=numpy.zeros(100)
        self.Errors.fill(numpy.nan)
        self.Heats = numpy.zeros(100)
        self.Heats.fill(numpy.nan)
        self.times = numpy.arange(100,0,-1)
        
    def _setup_signal_slots(self):
        
        self.newT_SpinBox.valueChanged.connect(self._update_newT)
        #QObject.connect(self.newT_SpinBox,SIGNAL("valueChanged(double)"),self._update_newT)
        self.P_SpinBox.valueChanged.connect(self._update_P)

        #QObject.connect(self.P_SpinBox,SIGNAL("valueChanged(double)"),self._update_P)
        self.I_SpinBox.valueChanged.connect(self._update_I)
        #QObject.connect(self.I_SpinBox,SIGNAL("valueChanged(double)"),self._update_I)
        self.D_SpinBox.valueChanged.connect(self._update_D)
        #QObject.connect(self.D_SpinBox,SIGNAL("valueChanged(double)"),self._update_D)

        self.Start.released.connect(self._start_aquisition)        
        #QObject.connect(self.Start,SIGNAL("released()"),self._start_aquisition)
        self.Quit.released.connect(self._quit_tip_gui)
        #QObject.connect(self.Quit,SIGNAL("released()"),self._quit_tip_gui)
    
    
    def _setup_views(self):
        self.Temp_view.setLabel('left',"Temperature / K")
        self.Temp_view.setLabel('bottom',"Time")
        self.Temp_view.plt = self.Temp_view.plot(pen='y')
        

        self.Heat_view.setLabel('left',"Heat / uW")
        self.Heat_view.setLabel('bottom',"Time")
        self.Heat_view.plt = self.Heat_view.plot(pen='y')
        
        self.Error_view.setLabel('left',"Error / uK ")
        self.Error_view.setLabel('bottom',"Time")
        self.Error_view.plt = self.Error_view.plot(pen='y')
        
        #for i in range(3):
        #    self.Temp_view.plot(x, y[i], pen=(i,3))
    
    def _update_newT(self,T):
        # #print "new T:",T
        # #print self.newT_SpinBox.value()
        # rc = remote_client(self.data)    
        # rc.send("set T "+str(T))
        # if not int(rc.recv().strip()) == 1:
        #     raise Error("communication error")
        # rc.close()
        set_param("mxc","control_temperature",T)


    def _quit_tip_gui(self):
        self.data.wants_abort = True
        sleep(0.2)
        exit()

    def _start_aquisition(self):
        #AQ  = AcquisitionThread(DATA)
        """ Callback of the "start stop acquisition" button. This starts
            the acquisition thread, or kills it/
        """
        if self.acquisition_thread and self.acquisition_thread.isAlive():
            self.data.wants_abort = True
        else:
            # connect the function calls
            self.acquisition_thread = AcquisitionThread(self.data)
            self.acquisition_thread.T_sig.connect(self._update_Temp)
            self.acquisition_thread.H_sig.connect(self._update_Heat)
            self.acquisition_thread.E_sig.connect(self._update_Error)
            
            self.acquisition_thread.T_sig.connect(self.T_field.setValue)
            self.acquisition_thread.H_sig.connect(self.H_field.setValue)
            self.acquisition_thread.R_sig.connect(self.R_field.setValue)
            
            self._update_PID_from_remote()
            self._update_control_temperature()
            self.acquisition_thread.start()
            

    def _update_P(self,P):
        self.data.P = P
        set_param("mxc","control_p",float(P))
        #print self.P_SpinBox.value()
    def _update_I(self,I):
        self.data.I = I
        set_param("mxc","control_i",float(I))

    def _update_D(self,D):
        self.data.D = D
        set_param("mxc","control_d",float(D))

    def _update_PID_from_remote(self):
    
        self.data.P = float(get_param("mxc","control_p"))
        self.data.I = float(get_param("mxc","control_i"))
        self.data.D = float(get_param("mxc","control_d"))
        self.P_SpinBox.setValue(self.data.P)
        self.I_SpinBox.setValue(self.data.I)
        self.D_SpinBox.setValue(self.data.D)

    def _update_control_temperature(self):
        self.data.set_T = float(get_param("mxc","control_temperature"))
        self.newT_SpinBox.setValue(self.data.set_T)
     
        
    @pyqtSlot(float)
    def _update_Temp(self,Temp):
        self.Temps = numpy.delete(numpy.append(self.Temps,Temp*1e3),0)
        self.Temp_view.plt.setData(x=self.times, y=self.Temps)#, pen=(1,3))
    @pyqtSlot(float)
    def _update_Heat(self,Heat):
        self.Heats = numpy.delete(numpy.append(self.Heats,Heat*1e6),0)
        self.Heat_view.plt.setData(self.times, self.Heats)#, pen=(1,3))
    @pyqtSlot(float)
    def _update_Error(self,Error):
        self.Errors=numpy.delete(numpy.append(self.Errors,Error*1e6),0)
        self.Error_view.plt.setData(self.times, self.Errors)

    @pyqtSlot(float)
    def _update_R(self,R):
        self.R_field.setValue(R)
        
    def _update_gui_values(self,T,R,Heat,Tctrl):
        self.T_field.setValue(T)
        self.R_field.setValue(R)
        self.H_field.setValue(Heat*1e6)
        #self.newT_SpinBox.setValue(Tctrl)
        
# Main entry to program.  Sets up the main app and create a new window.
def main(argv):
    # some configuration boilerplate
    data = DATA()
    parser = argparse.ArgumentParser(
        description="TIP Is not Perfect // HR@KIT 2011-2019")

    parser.add_argument('ConfigFile', nargs='?', default='settings_local.cfg',
                        help='Configuration file name')
    args=parser.parse_args()

    data.Conf = configparser.RawConfigParser(inline_comment_prefixes=';')
    data.Conf.read(args.ConfigFile)

    # create Qt application
    app = QApplication(argv)
    # create main window
    wnd = MainWindow(data) # classname
    wnd.show()
    
    # Connect signal for app finish
    app.lastWindowClosed.connect(quit)
    #app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
    
    # Start the app up
    sys.exit(app.exec_())
 
if __name__ == "__main__":
    main(sys.argv)

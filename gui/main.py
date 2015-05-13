import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from time import sleep

from tip_gui_lib import DATA, AcquisitionThread, remote_client
from tip_gui_cover import Ui_MainWindow

import argparse
import ConfigParser
import numpy

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
        self.acquisition_thread =False
        
        self.Temps =numpy.zeros(100)
        self.Errors=numpy.zeros(100)
        self.Heats = numpy.zeros(100)
        self.times = numpy.arange(100,0,-1)
        
    def _setup_signal_slots(self):
        
        
        QObject.connect(self.newT_SpinBox,SIGNAL("valueChanged(double)"),self._update_newT)
        
        QObject.connect(self.P_SpinBox,SIGNAL("valueChanged(double)"),self._update_P)
        QObject.connect(self.I_SpinBox,SIGNAL("valueChanged(double)"),self._update_I)
        QObject.connect(self.D_SpinBox,SIGNAL("valueChanged(double)"),self._update_D)
        
        QObject.connect(self.Start,SIGNAL("released()"),self._start_aquisition)    
        QObject.connect(self.Quit,SIGNAL("released()"),self._quit_tip_gui)
    
    
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
        #print "new T:",T
        #print self.newT_SpinBox.value()
        rc = remote_client(self.data)    
        rc.send("set T "+str(T))
        if not int(rc.recv().strip()) == 1:
            raise Error("communication error")
        rc.close()

    def _quit_tip_gui(self):
        self.data.wants_abort = True
        sleep(0.5)
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
            self._update_SET_temperature()
            self.acquisition_thread.start()
            

    def _update_P(self,P):
        self.data.P = P
        self._update_PID()
        #print self.P_SpinBox.value()
    def _update_I(self,I):
        self.data.I = I
        self._update_PID()
    def _update_D(self,D):
        self.data.D = D
        self._update_PID()
    def _update_PID(self):
       rc = remote_client(self.data)
       rc.send("set PID %.5f %.5f %.5f"% (self.data.P,self.data.I,self.data.D))
       if not int(rc.recv().strip()) == 1:
           raise Error("communication error")
       rc.close()
    def _update_PID_from_remote(self):
    
        rc = remote_client(self.data)
        
        rc.send("GET PID")
        pid_str=rc.recv().split()
        rc.close()
        self.data.P = float(pid_str[0])
        self.data.I = float(pid_str[1])
        self.data.D = float(pid_str[2])
        self.P_SpinBox.setValue(self.data.P)
        self.I_SpinBox.setValue(self.data.I)
        self.D_SpinBox.setValue(self.data.D)
    def _update_SET_temperature(self):
    
        rc = remote_client(self.data)
        
        rc.send("GET TCTRL")
        self.data.set_T = float(rc.recv())
        rc.close()

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

    def _update_gui_values(self,T,R,Heat,Tctrl):
        #print T
        self.T_field.setValue(T)
        self.R_field.setValue(R)
        self.H_field.setValue(Heat)
        #self.newT_SpinBox.setValue(Tctrl)
        
# Main entry to program.  Sets up the main app and create a new window.
def main(argv):
    # some configuration boilerplate
    data = DATA()
    parser = argparse.ArgumentParser(
        description="TIP Is not Perfect // HR@KIT 2011-2015")

    parser.add_argument('ConfigFile', nargs='?', default='settings_local.cfg',
                        help='Configuration file name')
    args=parser.parse_args()

    data.Conf = ConfigParser.RawConfigParser()
    data.Conf.read(args.ConfigFile)

    # create Qt application
    app = QApplication(argv,True)
    # create main window
    wnd = MainWindow(data) # classname
    wnd.show()
    
    # Connect signal for app finish
    app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
    
    # Start the app up
    sys.exit(app.exec_())
 
if __name__ == "__main__":
    main(sys.argv)

# tip regulation gui / HR@KIT 2011 - 2019
import sys

# make it pyqt5 only ...
#from PyQt4.QtCore import *
#from PyQt4.QtGui import *
from PyQt5.QtCore import * #Qt, QObject
from PyQt5.QtWidgets import * # QApplication
from PyQt5 import QtGui


from time import sleep
import pprint

from gui.tip_gui_lib import DATA, AcquisitionThread #,  remote_client
from gui.tip_gui_cover import Ui_MainWindow

import argparse
import configparser
import numpy


from lib.tip_zmq_client_lib import setup_connection, close_connection, get_config, get_param, set_param, set_exit


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

        self.tip_url = "tcp://localhost:5000"
        self.tip_connected = False
        #"tcp://localhost:5000"
        
        self.tip_conf = None
        self.thermometer = None
        self.new_thermometer = False
        self._set_view_containers()
        self.acquisition_thread =False
    
    def closeEvent(self, event):
        print ("window destroyed")
        self._quit_tip_gui()
        event.accept()

    def _set_view_containers(self):
        LENGTH = 0
        self.Temps  = numpy.empty(LENGTH)
        #self.Temps.fill(numpy.nan)
        self.Errors = numpy.zeros(LENGTH)
        #self.Errors.fill(numpy.nan)
        self.Heats  = numpy.zeros(LENGTH)
        #self.Heats.fill(numpy.nan)
        self.times  = numpy.zeros(LENGTH) #numpy.arange(LENGTH,0,-1)
    
    def _set_range_box(self,thermometer):
        self.rangeBox.clear()
        for drange in self.tip_conf[self.tip_conf[thermometer]['device']]['device_ranges']:
            self.rangeBox.addItem(drange)
    
    def _set_excitation_box(self,thermometer):
        self.excitationBox.clear()
        for drange in self.tip_conf[self.tip_conf[thermometer]['device']]['device_excitations']:
            self.excitationBox.addItem(drange)


    def _setup_signal_slots(self):
        
        self.newT_SpinBox.valueChanged.connect(self._update_newT)
        
        self.P_SpinBox.valueChanged.connect(self._update_P)
        self.I_SpinBox.valueChanged.connect(self._update_I)
        self.D_SpinBox.valueChanged.connect(self._update_D)

        self.Thermometer_box.currentIndexChanged.connect(self._thermometer_changed)
        
        self.rangeBox.currentIndexChanged.connect(self._range_changed)
        self.excitationBox.currentIndexChanged.connect(self._excitation_changed)

        #self.Connect.released.connect(self._connetc_to_tip)
        #self.Start.released.connect(self._start_aquisition)        

        self.action_TIP_server.triggered.connect(self._set_tip_server)
        self.actionQuit.triggered.connect(self._quit_tip_gui)
        self.actionTIP_Configuration.triggered.connect(self._display_config)
    
    
    def _setup_views(self):
        self.Temp_view.setLabel('left',"Temperature", units="K")
        self.Temp_view.setLabel('bottom',"Time", units="s")
        self.Temp_view.plt = self.Temp_view.plot(pen='y')

        self.Heat_view.setLabel('left',"Heat", units="W")
        self.Heat_view.setLabel('bottom',"Time",units="s")
        self.Heat_view.plt = self.Heat_view.plot(pen='y')
        
        self.Error_view.setLabel('left',"Error", units="K")
        self.Error_view.setLabel('bottom',"Time",units="s")
        self.Error_view.plt = self.Error_view.plot(pen='y')
        
    
    def _update_newT(self,T):
        print ("update new temperature")
        set_param(self.thermometer,"control_temperature",T)

    def _connetc_to_tip(self):
        setup_connection(self.tip_url)

        self.tip_connected = True
        self.statusbar.showMessage("Connected to: "+str(self.tip_url))

        self.tip_conf = get_config()
        self.data.tip_conf = self.tip_conf 

        self.Thermometer_box.clear()
        for thermometer in self.tip_conf['system']['active_thermometers']:
            self.Thermometer_box.addItem(thermometer)
        
        self._start_aquisition()
        
    
    def _set_tip_server(self):
        self.tip_url, ok = QInputDialog.getText(self, "Enter URL to TIP server ",
                                     "TIP server:", QLineEdit.Normal,
                                     "tcp://localhost:5000")
        if ok and self.tip_url:
            self._connetc_to_tip()
    
    def _display_config(self):
        tip_config = get_config()
        txt = pprint.pformat(tip_config, indent=4)
        msgBox = TextDisplay(self)
        msgBox.display(txt)
        msgBox.show()

    def _thermometer_changed(self):
        self.thermometer  = self.Thermometer_box.currentText()
        DATA.thermometer = self.thermometer
        self.new_thermometer = True
        self._set_view_containers()
        self._set_range_box(self.thermometer)
        self._set_excitation_box(self.thermometer)
        self.new_thermometer = False

        print(self.thermometer)

    def _range_changed(self,device_range):
        if not self.new_thermometer:
            set_param(self.thermometer,"device_range",device_range)
            print(device_range)

    def _excitation_changed(self,device_excitation):
        if not self.new_thermometer:
            set_param(self.thermometer,"device_excitation",device_excitation)
            print(device_excitation)        

    def _quit_tip_gui(self):
        print("Quitting TIP GUI")
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
            self.acquisition_thread.C_T_sig.connect(self._update_control_temperature)
            self.acquisition_thread.Int_sig.connect(self.Int_field.setValue)
                  

            self.acquisition_thread.P_sig.connect(self._update_P_from_remote)
            self.acquisition_thread.I_sig.connect(self._update_I_from_remote)
            self.acquisition_thread.D_sig.connect(self._update_D_from_remote)

            self.acquisition_thread.DR_sig.connect(self._update_range_from_remote)
            self.acquisition_thread.DE_sig.connect(self._update_excitation_from_remote)

            self.acquisition_thread.T_sig.connect(self.T_field.setValue)
            self.acquisition_thread.H_sig.connect(self.H_field.setValue)
            self.acquisition_thread.R_sig.connect(self.R_field.setValue)


            self.data.P = float(get_param(self.thermometer,"control_p"))
            self.data.I = float(get_param(self.thermometer,"control_i"))
            self.data.D = float(get_param(self.thermometer,"control_d"))
            self.P_SpinBox.setValue(self.data.P)
            self.I_SpinBox.setValue(self.data.I)
            self.D_SpinBox.setValue(self.data.D)

            self.data.control_T = float(get_param(self.thermometer,"control_temperature"))
            self.newT_SpinBox.setValue(self.data.control_T)

            self.acquisition_thread.start()
            

    def _update_P(self,P):
        #self.data.P = P
        set_param(self.thermometer,"control_p",float(P))

    def _update_I(self,I):
        #self.data.I = I
        set_param(self.thermometer,"control_i",float(I))

    def _update_D(self,D):
        #self.data.D = D
        set_param(self.thermometer,"control_d",float(D))

    def _update_P_from_remote(self,P):
        if not self.P_SpinBox.hasFocus():
            self.P_SpinBox.setValue(P)
    def _update_I_from_remote(self,I):
        if not self.I_SpinBox.hasFocus():
            self.I_SpinBox.setValue(I)
    def _update_D_from_remote(self,D):   
        if not self.D_SpinBox.hasFocus():
            self.D_SpinBox.setValue(D)       

    def _update_range_from_remote(self,R):
        if not self.rangeBox.hasFocus():
            self.rangeBox.setCurrentIndex(R)
    def _update_excitation_from_remote(self,E):   
        if not self.excitationBox.hasFocus():
            self.excitationBox.setCurrentIndex(E)     

    def _update_control_temperature(self,control_T):
        self.data.control_T = control_T
        if not self.newT_SpinBox.hasFocus():
            self.newT_SpinBox.setValue(control_T)


        
        
    @pyqtSlot(float)
    def _update_Temp(self,Temp):
        MAXLENGTH = 150
        if len(self.Temps) < MAXLENGTH:
            self.Temps = numpy.append(self.Temps,Temp)
        else:
            self.Temps = numpy.delete(numpy.append(self.Temps,Temp),0)
        times = numpy.arange(len(self.Temps),0,-1)
        self.Temp_view.plt.setData(x=times, y=self.Temps)#, pen=(1,3))

    @pyqtSlot(float)
    def _update_Heat(self,Heat):
        MAXLENGTH = 150
        if len(self.Heats) < MAXLENGTH:
            self.Heats = numpy.append(self.Heats,Heat)
        else:
            self.Heats = numpy.delete(numpy.append(self.Heats,Heat),0)
        times = numpy.arange(len(self.Heats),0,-1)
        self.Heat_view.plt.setData(times, self.Heats)#, pen=(1,3))

    @pyqtSlot(float)
    def _update_Error(self,Error):
        MAXLENGTH = 150
        if len(self.Errors) < MAXLENGTH:
            self.Errors = numpy.append(self.Errors,Error)
        else:
            self.Errors=numpy.delete(numpy.append(self.Errors,Error),0)

        times = numpy.arange(len(self.Errors),0,-1)
        
        self.Error_view.plt.setData(times, self.Errors)

    @pyqtSlot(float)
    def _update_R(self,R):
        self.R_field.setValue(R)
        
    def _update_gui_values(self,T,R,Heat,Tctrl):
        self.T_field.setValue(T)
        self.R_field.setValue(R)
        self.H_field.setValue(Heat*1e6)
        #self.newT_SpinBox.setValue(Tctrl)
    
class TextDisplay(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(TextDisplay, self).__init__(parent)
        self.TE = QTextEdit()
        self.setCentralWidget(self.TE)
        self.resize(400,500)
    def display(self,txt):
        self.TE.insertPlainText(txt)

        
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

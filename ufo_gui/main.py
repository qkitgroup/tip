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
        
        self.data.T = [numpy.zeros(10) for _ in range (5)]
        self.data.times = [numpy.zeros(10) for _ in range (5)]
        
        
    def _setup_signal_slots(self):
        QObject.connect(self.actionStart,SIGNAL("triggered()"),self._start_aquisition)    
        QObject.connect(self.b_auto,SIGNAL("triggered()"),self._autorange_plots)    
        QObject.connect(self.b_24,SIGNAL("triggered()"),self._range_24)
        QObject.connect(self.b_12,SIGNAL("triggered()"),self._range_12)
        QObject.connect(self.b_6,SIGNAL("triggered()"),self._range_6)
        QObject.connect(self.b_2,SIGNAL("triggered()"),self._range_2)
        QObject.connect(self.b_1,SIGNAL("triggered()"),self._range_1)
        QObject.connect(self.m_poll,SIGNAL("triggered()"),self._req_meas)
        
        QObject.connect(self.actionQuit,SIGNAL("triggered()"),self._quit_tip_gui)
        QObject.connect(self,SIGNAL("destroyed()"),self._quit_tip_gui)
    
    
    def _setup_views(self):
        self.Temp_view1.setLabel('left',"He-Bath / K")
        self.Temp_view1.setLabel('bottom',"Time")
        self.Temp_view1.plt = self.Temp_view1.plot(pen='y')
        
        self.Temp_view2.setLabel('left',"1K Pot / K")
        self.Temp_view2.setLabel('bottom',"Time")
        self.Temp_view2.plt = self.Temp_view2.plot(pen='y')
        
        self.Temp_view3.setLabel('left',"Still / K")
        self.Temp_view3.setLabel('bottom',"Time")
        self.Temp_view3.plt = self.Temp_view3.plot(pen='y')
        
        self.Temp_view4.setLabel('left',"Base / K")
        self.Temp_view4.setLabel('bottom',"Time")
        self.Temp_view4.plt = self.Temp_view4.plot(pen='y')
        
        self.Temp_view5.setLabel('left',"Intermediate / K")
        self.Temp_view5.setLabel('bottom',"Time")
        self.Temp_view5.plt = self.Temp_view5.plot(pen='y')
    
    def _update_newT(self,T):
        pass

    def _quit_tip_gui(self):
        self.data.wants_abort = True
        sleep(0.5)
        exit()
        
    def _start_aquisition(self):
        print "start triggered"
        #AQ  = AcquisitionThread(DATA)
        """ Callback of the "start stop acquisition" button. This starts
            the acquisition thread, or kills it/
        """
        if self.acquisition_thread and self.acquisition_thread.isAlive():
            self.data.wants_abort = True
        else:
            # connect the function calls
            self.m_poll.setEnabled(True)
            self.acquisition_thread = AcquisitionThread(self.data)
            self.acquisition_thread.update_sig.connect(self._update_gui)
            self.acquisition_thread.start()
    
    def _autorange_plots(self):
        for i in range(5):
            exec("self.Temp_view%i.enableAutoRange()"%(i+1))
        
    def _range_plots(self,rang):
        for i in range(5):
            yRange= [numpy.min(self.data.T[i][numpy.where((self.data.times[i][-1]-self.data.times[i])<rang*3600)]),numpy.max(self.data.T[i][numpy.where((self.data.times[i][-1]-self.data.times[i])<rang*3600)])]
            exec("self.Temp_view%i.setRange(xRange=[-rang,0],yRange=yRange)"%(i+1))
            
            
    
    def _range_24(self): self._range_plots(24)
    def _range_12(self): self._range_plots(12)
    def _range_6(self): self._range_plots(6)
    def _range_2(self): self._range_plots(2)
    def _range_1(self): self._range_plots(1)
    
    def _req_meas(self): self.acquisition_thread.acquire_from_remote("set/therm/:/schedule",delay=.2)
    
     
        
    @pyqtSlot(float)
    def _update_gui(self):
        self.Temp_view1.plt.setData(x=(self.data.times[0]-self.data.times[0][-1])/3600, y=self.data.T[0])
        self.Temp_view2.plt.setData(x=(self.data.times[1]-self.data.times[1][-1])/3600, y=self.data.T[1])
        self.Temp_view3.plt.setData(x=(self.data.times[2]-self.data.times[2][-1])/3600, y=self.data.T[2])
        self.Temp_view4.plt.setData(x=(self.data.times[3]-self.data.times[3][-1])/3600, y=self.data.T[3])
        self.Temp_view5.plt.setData(x=(self.data.times[4]-self.data.times[4][-1])/3600, y=self.data.T[4])
        
        self.T1a_field.setSuffix(" "+("m" if self.data.T[0][-1]<.8 else "")+"K")
        self.T1a_field.setValue(self.data.T[0][-1]*(1e3 if self.data.T[0][-1]<.8 else 1 ))
        self.T2_field.setSuffix(" "+("m" if self.data.T[1][-1]<.8 else "")+"K")
        self.T2_field.setValue(self.data.T[1][-1]*(1e3 if self.data.T[1][-1]<.8 else 1 ))
        self.T3_field.setSuffix(" "+("m" if self.data.T[2][-1]<.8 else "")+"K")
        self.T3_field.setValue(self.data.T[2][-1]*(1e3 if self.data.T[2][-1]<.8 else 1 ))
        self.T4_field.setSuffix(" "+("m" if self.data.T[3][-1]<.8 else "")+"K")
        self.T4_field.setValue(self.data.T[3][-1]*(1e3 if self.data.T[3][-1]<.8 else 1 ))
        self.T5_field.setSuffix(" "+("m" if self.data.T[4][-1]<.8 else "")+"K")
        self.T5_field.setValue(self.data.T[4][-1]*(1e3 if self.data.T[4][-1]<.8 else 1 ))
        
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

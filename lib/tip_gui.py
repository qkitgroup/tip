#!/usr/bin/env python
# TIP GUI version 0.1 written by HR@KIT  Nov 2010


import numpy

import wxversion
wxversion.ensureMinimal('2.8')


import matplotlib
matplotlib.use("WxAgg")
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure


# for gui
import wx


import time
import thread

EVT_RESULT_ID = wx.NewId()
def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)
    
class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self,id):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.id = id



class AppFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self.debug = True
        self.started = False
        
        # init pid class
        self.pid = kwds.pop("PID")
        self.DATA = kwds.pop("DATA")
        self.time = numpy.arange(100)

        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.PLabel = wx.StaticText(self, -1, " P: ")
        self.P_txcntl = wx.TextCtrl(self, -1, str(self.pid.P),style=wx.TE_PROCESS_ENTER)
        self.ILabel = wx.StaticText(self, -1, " I: ")
        self.I_txcntl = wx.TextCtrl(self, -1, str(self.pid.I),style=wx.TE_PROCESS_ENTER)
        self.DLabel = wx.StaticText(self, -1, " D: ")
        self.D_txcntl = wx.TextCtrl(self, -1, str(self.pid.D),style=wx.TE_PROCESS_ENTER)

        self.TargetRate = wx.StaticText(self, -1, " Target Temperature: ")
        self.TargetRate_txcntl = wx.TextCtrl(self, -1, "0.001",style=wx.TE_PROCESS_ENTER)

        self.StartButton = wx.ToggleButton(self, -1, "Start control")
        self.HoldButton = wx.ToggleButton(self, -1, "Hold")
        self.QuitButton = wx.Button(self, -1, "Quit")
        self.L_depRate = wx.StaticText(self, -1, "Temperature")
        self.L_DepRate_val = wx.StaticText(self, -1, "")
        self.L_Current = wx.StaticText(self, -1, "Heat")
        self.L_Current_val = wx.StaticText(self, -1, "")
        self.L_PID_Error = wx.StaticText(self, -1, "PID Error")
        self.L_PID_Error_val = wx.StaticText(self, -1, "")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_TEXT_ENTER, self._set_P, self.P_txcntl)
        self.Bind(wx.EVT_TEXT_ENTER, self._set_I, self.I_txcntl)
        self.Bind(wx.EVT_TEXT_ENTER, self._set_D, self.D_txcntl)
        self.Bind(wx.EVT_TEXT_ENTER, self._set_TargetRate, self.TargetRate_txcntl)
        self.Bind(wx.EVT_TOGGLEBUTTON, self._set_start, self.StartButton)
        self.Bind(wx.EVT_TOGGLEBUTTON, self._set_hold, self.HoldButton)
        self.Bind(wx.EVT_BUTTON, self._set_Quit, self.QuitButton)

        # thread handler, connect signals to receivers
        EVT_RESULT(self,self.update_gui)

        # one thread which update the display with signals. not very fancy
        thread.start_new_thread(self.trigger_update,((self,)))


    def __set_properties(self):
        self.SetTitle("Temperature PID Control")

    def __do_layout(self):

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_mpl = wx.BoxSizer(wx.HORIZONTAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_7_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_7_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_7_0 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add(self.PLabel, 0, 0, 0)
        sizer_3.Add(self.P_txcntl, 0, 0, 0)
        sizer_3.Add(self.ILabel, 0, 0, 0)
        sizer_3.Add(self.I_txcntl, 0, 0, 0)
        sizer_3.Add(self.DLabel, 0, 0, 0)
        sizer_3.Add(self.D_txcntl, 0, 0, 0)
        sizer_3.Add(self.TargetRate, 0, 0, 0)
        sizer_3.Add(self.TargetRate_txcntl, 0, 0, 0)
        sizer_2.Add(sizer_3, 1, 0, 0)
        sizer_4.Add(self.StartButton, 0, 0, 0)
        sizer_4.Add(self.HoldButton, 0, 0, 0)
        sizer_4.Add(self.QuitButton, 0, 0, 0)
        sizer_2.Add(sizer_4, 1, 0, 0)
        sizer_7_0.Add(self.L_depRate, 0, 0, 0)
        sizer_7_0.Add(self.L_DepRate_val, 0, 0, 0)
        sizer_6.Add(sizer_7_0, 1, 0, 0)
        sizer_6.Add((20, 20), 0, 0, 0)
        sizer_7_1.Add(self.L_Current, 0, 0, 0)
        sizer_7_1.Add(self.L_Current_val, 0, 0, 0)
        sizer_6.Add(sizer_7_1, 1, 0, 0)
        sizer_6.Add((20, 20), 0, 0, 0)
        sizer_7_2.Add(self.L_PID_Error, 0, 0, 0)
        sizer_7_2.Add(self.L_PID_Error_val, 0, 0, 0)
        sizer_6.Add(sizer_7_2, 0, 0, 0)
        sizer_2.Add(sizer_6, 0, 0, 0)
        sizer_2.Add(sizer_mpl, 0, wx.EXPAND, 1)
        # mpl
        self.figure = Figure(figsize=(6,5))
        self.figure.subplots_adjust(wspace=0.5,hspace=0.5)
        self.axes_Rate = self.figure.add_subplot(311)
        self.axes_Curr = self.figure.add_subplot(312,sharex=self.axes_Rate)
        self.axes_pidE = self.figure.add_subplot(313,sharex=self.axes_Rate)
      
        self.axes_pidE.set_ylabel("PID Error")
        self.axes_Curr.set_ylabel("Heat")
        self.axes_Rate.set_ylabel("T")
        
        self.axes_pidE.set_xlabel("time")
        
        self.canvas = FigureCanvas(self, -1, self.figure)
        sizer_mpl.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)

        self.SetSizer(sizer_2)
        sizer_2.Fit(self)
        self.Layout()
        


    def _set_P(self, event):
        if self.debug: print "set P to:",self.P_txcntl.GetValue()
        self.pid.set_P(float(self.P_txcntl.GetValue()))
    def _set_I(self, event): 
        if self.debug: print "set I to:",self.I_txcntl.GetValue()
        self.pid.set_P(float(self.I_txcntl.GetValue()))
    def _set_D(self, event): 
        if self.debug: print "set D to:",self.D_txcntl.GetValue()
        self.pid.set_P(float(self.D_txcntl.GetValue()))
    def _set_TargetRate(self,event):
        if self.debug: print "set Target Temperature to:",self.TargetRate_txcntl.GetValue()
        self.pid.set_target_temperature(float(self.TargetRate_txcntl.GetValue()))
        #event.Skip()

    def _set_start(self, event): 
        if self.StartButton.GetValue():
            if self.debug: print "start pressed"
            self.StartButton.SetLabel("Stop")
            self.started = True
        else:
            if self.debug: print "stop pressed"
            self.StartButton.SetLabel("Start")
            self.started = False
            
    def _set_hold(self, event): 
        if self.HoldButton.GetValue():
            if self.debug: print "hold pressed"
            self.HoldButton.SetLabel("holding")
            self.pid.set_hold(state=True)
        else:
            if self.debug: print "un-hold pressed"
            self.HoldButton.SetLabel("Hold")
            self.pid.set_hold(state=False)

    def _set_Quit(self, event): 
        print "Going down ..."
        self.DATA.Running = False
        time.sleep(1)
        self.Destroy()

    def trigger_update(self,notify_window):
        # trigger_update runs in a separate thread
        # and sends occasionally a signal to update the gui
        # the thread dies when return is called
        # Fixme: checking a global variable is not very elegant for
        # ending the thread but for now ...
         while True:
            if self.started:
                if not self.DATA.Running: return
                # send signal to update labels(id=1) and plot(id=2)
                wx.PostEvent(notify_window, ResultEvent(1))
                time.sleep(0.5)
                wx.PostEvent(notify_window, ResultEvent(1))
                wx.PostEvent(notify_window, ResultEvent(2))
            time.sleep(0.5)
            
            
    def update_gui(self,event):
        if event.id == 1:
            #this is the labels
            self.L_DepRate_val.SetLabel(str(round(self.DATA.get_lastTemp()*1000,2)))
            self.L_Current_val.SetLabel(str(round(self.DATA.get_lastHeat(),3)))
            self.L_PID_Error_val.SetLabel(str(round(self.DATA.get_lastError(),3)))

        if event.id == 2:
            # this is the plots
            self.axes_pidE.clear()
            self.axes_pidE.plot(self.time,self.DATA.get_pidE())
            self.axes_Curr.clear()
            self.axes_Curr.plot(self.time,self.DATA.get_Heat())
            self.axes_Rate.clear()
            self.axes_Rate.plot(self.time,self.DATA.get_Temp()*1000)

            # axes.clear also removes the labels, set again.
            self.axes_pidE.set_ylabel("PID Error")
            self.axes_Curr.set_ylabel("Heat")
            self.axes_Rate.set_ylabel("Temperature")
            self.axes_pidE.set_xlabel("time")

            self.canvas.draw()
        

if __name__ == "__main__":


    app = wx.PySimpleApp(0)
    mainFrame = AppFrame(None, -1, "")
    app.SetTopWindow(mainFrame)
    mainFrame.Show()
    app.MainLoop()


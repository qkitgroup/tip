#!/usr/bin/env python
#TIP main version 0.1 written by HR@KIT Nov 2010

import ConfigParser
import lib.tip_pidcontrol as tip_pidcontrol
import sys,time
import argparse
#from lib.tip_gui import *
from lib.tip_dev import *

from lib.tip_data import DATA

# server thread to spread information
import server.tip_srv_thread as tip_srv


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TIP Temperature Information Program HR@KIT 2011")

    parser.add_argument('ConfigFile', nargs='?', default='settings.cfg',
                        help='Configuration file name')
    args=parser.parse_args()
    
    Conf = ConfigParser.RawConfigParser()
    Conf.read(args.ConfigFile)
    
    DATA = DATA(Conf)
    DATA.config = Conf
    
    

    PID = tip_pidcontrol.pidcontrol(DATA)
    DATA.PID = PID

    IO = IO_worker(DATA) 
    IO.setDaemon(1)
    IO.start()
    
    tipserv = tip_srv.tip_srv(DATA)
    tipserv.loop()

"""    
    app = wx.PySimpleApp(0)
    mainFrame = AppFrame(None, -1, "",PID=PID,DATA=DATA)
    app.SetTopWindow(mainFrame)
    mainFrame.Show()
    app.MainLoop()
"""

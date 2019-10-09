#!/usr/bin/env python
#TIP main, version 1.5 written by HR@KIT Feb 2019
# TIP Is not Precious
import configparser
#import lib.tip_pidcontrol as tip_pidcontrol
import sys,time
import argparse

from lib.tip_dev import *

from lib.tip_init import tip_init

from lib.tip_data import DATA

# server thread to spread information
import server.tip_srv_thread as tip_srv


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TIP Is not Perfect // TIPteam 2019")

    parser.add_argument('ConfigFile', nargs='?', default='settings_local.cfg',
                        help='Configuration file name')
    args=parser.parse_args()
    
    
    config = tip_init(args.ConfigFile)
    #DATA = DATA(Conf)
    #DATA.config = Conf

    #PID = tip_pidcontrol.pidcontrol(DATA)
    #DATA.PID = PID

    #IO = IO_worker(DATA) 
    #IO.setDaemon(1)
    #IO.start()
    
    tipserv = tip_srv.tip_srv(DATA)
    tipserv.loop()


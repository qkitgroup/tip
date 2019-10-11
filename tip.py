#!/usr/bin/env python
# TIP main, version 1.5 written by HR@KIT 2019
# TIP Is not Precious

import argparse

from lib import tip_init



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TIP Is not Perfect // TIPteam 2019")

    parser.add_argument('ConfigFile', nargs='?', default='settings_local.cfg',
                        help='Configuration file name')
    args=parser.parse_args()
    
    print ("This is TIP / Temperature Information Program version 1.5 2010 - 2019")    
    tip_init.tip_init(args.ConfigFile)

    


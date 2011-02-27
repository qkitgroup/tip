# abstract tip R_Bridge class , written by HR @ KIT 2010
import random
import time, sys
import atexit
import tip_eich as TE

class R_bridge(object):
    "select a Bridge, and get resistance values from it"
    def __init__(self,DATA):
        self.config = DATA.config
        self.dummymode = self.config.getboolean('debug','dummymode')
        
        # import calibration class
        
        # import cal setting from settings.cfg
        self.CP = TE.TIPEich(
            self.config.get('Calibration','Name'),
            self.config.get('Calibration','FName'),
            self.config.get('Calibration','FOrder'),
            self.config.get('Calibration','Interpolation')
        )
        print "Done."
        print "Open and setup Bridge, may take a couple of seconds..."        
        # import bridge hardware class 
        import devices.Picowatt_AVS47 as AVS
        self.AVS = AVS

        if not self.dummymode:
            # init from config file
            self.setup_device()
            #sys.exit()
            print "Done."
        else:
            print "Bridge dummymode enabled: Done."
        
        # make sure that we gracefully go down
        atexit.register(self.disconnect)
        
    def setup_device(self):
        if self.config.get('RBridge','Com_Method').strip() == 'Ethernet':
            self.BR = self.AVS.Picowatt_AVS47(
                self.config.get('RBridge','Name'),
                'GPIB::'+self.config.get('RBridge','GPIB_Addr').strip(),
                ip=self.config.get('RBridge','IP'),
                delay=self.config.getfloat('RBridge','delay'),
                )
        else:
            self.BR = self.AVS.Picowatt_AVS47(
                self.config.get('RBridge','Name'),
                'GPIB::'+self.config.get('RBridge','GPIB_Addr').strip(),
                delay=self.config.getfloat('RBridge','delay'),
                )
            
        # basic setup
        self.BR._open()
        self.BR._set_remote()
        # set avs bridge from zero to measure, if not already there
        self.BR._set_input(1)
        
        # channel, excitation, range : avs specific, so far
        self.BR._set_channel(self.config.getint('RBridge','default_channel'),
                             self.config.getint('RBridge','default_excitation'),
                             self.config.getint('RBridge','default_range')
                             )

    def get_R(self):
        if not self.dummymode:
            #return self.BR._get_testR(init_R=10000)
            #R = self.BR._get_adc()
            R = self.BR._get_ave() # two averages ....
            #print R
            return float(R)
        else:
            return random.random()*100+10000

    def get_T_from_R(self, R):
        return self.CP.getT_from_R(R)
    def get_T(self):
        if not self.dummymode:
            return self.get_T_from_R(self.get_R())
        else:
            # in dummymode we get 100mK + some random mK
            return random.random()/100+0.1
    def set_Range(self,Range):
        return self.BR._set_range(Range)
        
    def disconnect(self):
        if not self.dummymode:
            print "disconnecting the bridge ..."
            self.BR._set_local()
            self.BR._close() 

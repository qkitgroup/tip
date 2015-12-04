# abstract tip R_Bridge class , written by HR @ KIT 2010
import random
import time, sys
import atexit
import numpy as np

class R_bridge(object):
    "select a Bridge, and get resistance values from it"
    def __init__(self,DATA):
        self.config = DATA.config
        self.DATA = DATA
        self.dummymode = self.config.getboolean('debug','dummymode')

        print "Open and setup Bridge, may take a couple of seconds..."
        # import bridge hardware class
        if self.config.get('RBridge','Name').strip() == 'PW_AVS47':
            if not self.dummymode:
                print "Initializing AVS47 ..."
                # init from config file
                self.setup_device_AVS47()
                #sys.exit()
                print "Done."
            
        elif self.config.get('RBridge','Name').strip() == 'SRS_SIM900':
            
            if not self.dummymode:
                print "Initializing SIM921 ..."
                # init from config file
                self.setup_device_SIM921()
                #sys.exit()
                print "Done."
            else:
                self.BR = None
        elif self.config.get('RBridge','Name').strip() == 'Lakeshore_370':
            if not self.dummymode:
                print "Initializing Lakeshore 370..."
                # init from config file
                self.setup_device_LS370()
                #sys.exit()
                print "Done."
        elif self.config.get('RBridge','Name').strip() == 'Dummy':
            from devices.dummy import DummyDevice
            self.BR = DummyDevice()
            print "Dummy bridge init"
        else:
            print 'Warning:no bridge enabled!'
        print "Bridge enabled: Done."
        
        # make sure that we gracefully go down
        atexit.register(self.disconnect)
        
    def setup_device_AVS47(self):
        import devices.Picowatt_AVS47 as AVS
        
        if self.config.get('RBridge','Com_Method').strip() == 'Ethernet':
            self.BR = AVS.Picowatt_AVS47(
                self.config.get('RBridge','Name'),
                'GPIB::'+self.config.get('RBridge','GPIB_Addr').strip(),
                ip=self.config.get('RBridge','IP'),
                delay=self.config.getfloat('RBridge','delay'),
                )
        else:
            pass
        """
            self.BR = AVS.Picowatt_AVS47(
                self.config.get('RBridge','Name'),
                'GPIB::'+self.config.get('RBridge','GPIB_Addr').strip(),
                delay=self.config.getfloat('RBridge','delay'))
        """
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
        
        

        
    def setup_device_SIM921(self):
        import devices.SRS_SIM900 as SIM
        """def __init__(self,ip= ,gpib="GPIB::0",SIM921_port=6,SIM925_port=8):"""
        if self.config.get('RBridge','Com_Method').strip() == 'Ethernet':
            self.BR = SIM.SIM900(
                self.config.get('RBridge','Name'),
                gpib='GPIB::'+self.config.get('RBridge','GPIB_Addr').strip(),
                ip=self.config.get('RBridge','IP'),
                delay=self.config.getfloat('RBridge','delay'),
                SIM921_port=self.config.getint('RBridge','SIM921_port'), #6 Bridge
                SIM925_port=self.config.getint('RBridge','SIM925_port'), #8 multiplexer
                SIM928_port=self.config.getint('RBridge','SIM928_port')         
                )
        else:
            pass
        
    def setup_device_LS370(self):
        import devices.Lakeshore_370 as LS370
        """def __init__(self,ip= ,gpib="GPIB::0"):"""
        if self.config.get('RBridge','Com_Method').strip() == 'Ethernet':
            self.BR = LS370.Lakeshore_370(
                self.config.get('RBridge','Name'),
                gpib='GPIB::'+self.config.get('RBridge','GPIB_Addr').strip(),
                ip=self.config.get('RBridge','IP'),
                delay=self.config.getfloat('RBridge','delay')
                )
            print 'LS enabled'
        else:
            print 'Lakeshore 370 not setup'
            pass

    def get_R(self):
        if not self.dummymode:
            #R = self.BR._get_adc()
            R = self.BR._get_ave() # two averages ....
            return float(R)
        else:
            return random.random()*100+10000

    # def get_T_from_R(self, R):
        # #if self.DATA.bridge.tainted:
        # #    return np.nan
        # #else:
        # #    return self.CP[self.DATA.bridge.get_Channel()].getT_from_R(R)
        # for i in range(20):
            # if not self.DATA.bridge.tainted:
                # return self.CP[self.DATA.bridge.get_Channel()].getT_from_R(R)
            # time.sleep(1)
            # print "DATA is tainted."
        # print "Within 10 seconds, tainted did not turn false, returning data anyway..."
        # return self.CP[self.DATA.bridge.get_Channel()].getT_from_R(R)
    def get_T(self):
        if not self.dummymode:
            # the LS370 does the interpolation by itself
            if self.config.get('RBridge','Name').strip() == 'Lakeshore_370':
                return self.BR.get_T()
            else:
                raise "Get T only implemented for Lakeshore 370"
        else:
            # in dummymode we get 100mK + some random mK
            return random.random()/100+0.1
    def set_Range(self,Range):
        return self.BR._set_range(Range)
        
    def set_Channel(self,Channel): #Channel is a TEMPERATURE Object
        print "-> %s:             waiting %.1fs"%(Channel.channel,Channel.settling_time)
        self.BR._set_Excitation(-1) #-1 is excitation off for SIM900
        self.BR._set_Channel(Channel.channel)
        self.BR._set_Range(Channel.range)
        self.BR._set_Excitation(Channel.excitation)
        return self.BR._get_Channel()==Channel.channel
        
    def disconnect(self):
        if not self.dummymode:
            print "disconnecting the bridge ..."
            self.BR._set_local()
            self.BR._close() 

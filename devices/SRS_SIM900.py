#!/usr/bin/env python

"""
SIM900 (Frame)
SIM921/SIM925(Bridge/MUX)
# SIM928 (Voltage Source)
Interface SIM921 resistance bridge. 
Changelog:
   HR@KIT 2013, 2014, AS@KIT 2015
   HR@KIT 2022 major update for TIP 2 and python 3.x
"""
import sys
from threading import Lock
import time
import logging
import visa_prologix as visa

def driver(name):
    print("entering driver", flush = True)
    SIM = SIM900(name,
                address     = config[name]['address'],
                delay       = config[name]['delay'],
                timeout     = config[name]['timeout'],
                gpib        = config[name]['gpib'],
                SIM921_port = config[name]['SIM921_port'],
                SIM925_port = config[name]['SIM925_port'])

    config[name]['device_ranges']       = SIM900.ranges
    config[name]['device_excitations']  = SIM900.excitations
    config[name]['device_integrations'] = SIM900.integrations
    return SIM

class SIM900(object):
    # Fixme:port
    def __init__(self,
                 name,
                 address = "",
                 delay = 0.2, 
                 gpib = "GPIB::0",
                 SIM921_port = 6,
                 SIM925_port = 8,
                 SIM928_port = 2  # <- this is not implemented anymore (for now)
                 ):
        
        self.SIM         = visa.instrument(gpib, ip = address, delay = delay)
        self.SIM921_port = SIM921_port
        self.SIM925_port = SIM925_port
        self.SIM928_port = SIM928_port
        #  mutex locks
        self.ctrl_lock   = Lock()

        #print "params",ip,gpib,delay,SIM921_port,SIM925_port,SIM928_port
        """    
        exci={0:-1, 3:0, 10:1, 30:2, 100:3, 300:4, 1000:5, 3000:6, 10000:7, 30000:8}
        rang={0.02:0, 0.2:1, 2:2, 20:3, 200:4, 2000:5, 20000:6, 200000:7, 2000000:8, 20000000:9}
        tcon={0:-1, 0.3:0, 1:1, 3:2, 10:3, 30:4, 100:5, 300:6}
        """
        self.ranges = [ # Ohm
                0.02, 
                0.2, 
                2, 
                20, 
                200, 
                2000, 
                20000, 
                200000, 
                2000000, 
                20000000
            ]

        self.excitations = [ # uV
                #0:-1, 
                3, 
                10, 
                30, 
                100, 
                300, 
                1000, 
                3000, 
                10000, 
                30000
            ]

        self.integrations = [ # seconds
                #0:-1, 
                0.3, 
                1, 
                3, 
                10, 
                30, 
                100, 
                300
            ]
    

    def get_IDN(self,port):
        cmd = "*IDN?"
        return (self.get_value_from_SIM900(port,cmd)).strip()
        

    def get_channel(self):
        """
        Gets the channel that is used to measure the resistance of the thermometer.

        Parameters
        ----------
        None

        Returns
        -------
        channel: int,int
            Number of channel that is connected to the thermometer.
        """
        
        port  = self.SIM925_port
        cmd = "CHAN?"
        
        try:
            channel = int(self.get_value_from_SIM900(port,cmd))
        except ValueError:
            print ("Value Error at get_channel, channel may not be set correctly")
            return False

        logging.debug('Get current channel: {:d}'.format(channel))
        return channel



    def set_channel(self, channel):
        """
        Sets the channel that is used to measure the resistance of the thermometer.

        Parameters
        ----------
        channel: int
            Number of channel that is connected to the thermometer.

        Returns
        -------
        None
        """
        
        current_channel = self.get_channel()
        if current_channel == channel:
            # do nothing
            pass
        else:
            logging.debug('Set channel to {:d}.'.format(channel))
            port  = self.SIM925_port
            cmd = "CHAN%i;CHAN?"%(channel)
            try:
                channel = int(self.get_value_from_SIM900(port,cmd))
            except ValueError:
                logging.error("Value Error at set_channel, channel may not be set correctly")
        self._channel = channel

    def get_excitation(self):
        """
        Gets the excitation value of the set channel.

        Parameters
        ----------
        None

        Returns
        -------
        val: int
            Excitation value of the bias with which the resistance of the thermometer is measured.
        """
       
        cmd = "EXCI?"
        excitation = self.get_value_from_SIM900(port,cmd)
       
        logging.debug('Get excitation of (current) channel {:d}: {:d} ({!s}) uV.'
            .format(channel, excitation, self.excitations[excitation]))
        return excitation

    def set_excitation(self, excitation):
        """
        Sets the excitation value of the set channel.

        Parameters
        ----------
        excitation: float
            Excitation value of the bias with which the resistance of the thermometer is measured.

        Returns
        -------
        None
        """
    
        if current_excitation == excitation:
            # do nothing
            return
        else:
            port  = self.SIM921_port
            #cmd = "EXCI %i;EXCI?"%(ex)
            #return int(self.get_value_from_SIM900(port,cmd))
            cmd = "EXCI %i"%(excitation)
            self.set_value_on_SIM900(port,cmd)
            logging.debug('Set excitation of channel {!s} to {!s}.'
                .format(self._channel, excitation))
        
    
    def get_range(self):
        """
        Gets the resistance measurement range of the set channel.

        Parameters
        ----------
        None

        Returns
        -------
        range: int
            Resistance measurement range for the thermometer.
        """
        # Corresponding command: <mode>,<excitation>,<range>,<autorange>,<cs off>[term] = RDGRNG? <channel>[term]
    
        cmd = "RANG?"
        r_range = self.get_value_from_SIM900(port,cmd)

        logging.debug('Get range of (current) channel {:d}: {:d} ({!s} Ohm).'
            .format(channel, r_range,self.resistances[r_range]))
        return r_range

    def set_range(self, r_range):
        """
        Sets the resistance measurement range of the set channel.

        Parameters
        ----------
        range: float
            Resistance measurement range for the thermometer. 'auto' is -1.

        Returns
        -------
        None
        """
        

        if r_range == -1:  # autorange
            autorange = 1
            time.sleep(3)

        elif r_range == current_r_range:
            # do nothing
            return
        else:
            port  = self.SIM921_port
            #cmd = "RANG%i;RANG?"%(range)
            #return int(self.get_value_from_SIM900(port,cmd))
            cmd = "RANG%i"%(r_range)
            self.set_value_on_SIM900(port,cmd)
            logging.debug('Set range of channel {:d} to {:d} ({!s}).'
            .format(channel, r_range,self.resistance_ranges[r_range]))
        
            time.sleep(3)


    def get_resistance(self):
        """
        Gets the resistance value of the thermometer that is connected to the set channel.

        Parameters
        ----------
        None

        Returns
        -------
        resistance: float
            Resistance of the thermometer.
        """    
        logging.debug('Get resistance of channel {:d}.'.format(channel))
        
        port  = self.SIM921_port
        cmd = 'RVAL?'
        # not sure if we need this, quite clumsy:
        for i in range(3):
            try: #andre 2015-04-02
                return float(self.get_value_from_SIM900(port,cmd))
            except ValueError:
                continue
        return None

        

        return resistance

    def set_integration(self, integration):
        """
        Sets the integration for the resistance measurement of the set channel.

        Parameters
        ----------
        integration: float
            Integration that composes of integration time and those averages.

        Returns
        -------
        None
        """
        

        if settle_time == integration:
            # do nothing
            return
        else:
        
            logging.debug('Set integration of channel {!s} to {!s}.'.format(self._channel, integration))
        self._integration_time = integration
    
    def get_integration(self):
        """
        Gets the integration for the resistance measurement of the set channel.

        Parameters
        ----------
        None

        Returns
        -------
        integration: float
            Integration, that composes of integration time and those averages.
        """
        # Corresponding command: #<off/on>,<settle time>,<window>[term] = FILTER? <channel>[term]
        try:
            logging.debug('Get integration of channel {!s}.'.format(self._channel))
            return self._integration
        except Exception as err:
            logging.error('Cannot get integration. Return last value instead. {!s}'.format(err))
            return self._integration
    
    def setup_device(self):
        pass
    def SIM_prolog(self,port = 0, init = False):
        try:
            # commands to mainframe
            self.SIM.write('main_esc')
            # flush output queue of SIM900
            self.SIM.write('FLOQ')
            if init:
                self.SIM.write('*CLS')
                self.SIM.write('*RST')
                self.SIM.write('CEOI ON') 
                self.SIM.write('EOIX ON')
            self.SIM.write('CONN '+str(port)+', "main_esc"')
        except:
            self.error('No Connection to SIM900 MAINFRAME up to main_esc')
    
    def SIM_epilog(self):
        self.SIM.write('main_esc')
    
    def get_value_from_SIM900(self,port,cmd):
        with self.ctrl_lock:
            for i in range(50): #try 50 times, Andre 2015-05-31
                try:
                    self.SIM_prolog(port)
                    val = self.SIM.ask(str(cmd))
                    #float(val) #only to catch the error, if this can not be converted to float #but not all are float!
                    self.SIM_epilog()
                    return val
                except Exception as e:
                    logging.debug(">>>Error #%i,%s: trying again '%s' on port %i"%(i,e,cmd,port))
                    time.sleep(.5)
                    continue
            return False
    def set_value_on_SIM900(self,port,cmd):
        with self.ctrl_lock:
            self.SIM_prolog(port)
            self.SIM.write(str(cmd))
            self.SIM_epilog()
    
    def _get_IDN(self,port):
        cmd = "*IDN?"
        return (self.get_value_from_SIM900(port,cmd)).strip()
        
    """ 
    def get_Rval(self):
        port  = self.SIM921_port
        cmd = 'RVAL?'
        for i in range(3):
            try: #andre 2015-04-02
                return float(self.get_value_from_SIM900(port,cmd))
            except ValueError:
                continue
        return None
    """

    
    """
        ########################################################
        # commands for the SIM298 isolated voltage source
        # (likely to be used as a heater ;-) )
        ########################################################
    def get_Voltage(self):
            port = self.SIM928_port
            cmd = "VOLT?"
            try:
               return float(self.get_value_from_SIM900(port,cmd))
            except ValueError:
               print "Value Error at get_Voltage, channel may not be set correctly"
               return False
    def set_Voltage(self,voltage):
           port = self.SIM928_port
           cmd = "VOLT "+str(voltage)
           self.set_value_on_SIM900(port,cmd)
    def set_output0(self,OUT_Volt): # HEATER interface
           self.set_Voltage(OUT_Volt)
    def set_output_ON(self):
           port = self.SIM928_port
           cmd = "OPON; EXON?"
           return self.get_value_from_SIM900(port,cmd)
    def set_output_OFF(self):
           port = self.SIM928_port
           cmd = "OPOF; EXON?"
           return self.get_value_from_SIM900(port,cmd)
    """

if __name__ == "__main__":
    # port 6 is the port to the SRS SIM921 bridge, port 8 is the SIM925 multiplexer
    SIM = SIM900("SIM900", address="10.22.197.34", SIM921_port=2,SIM925_port=1,) 
    print ("--- *IDN? ---")
    print (SIM._get_IDN(1))
    print (SIM._get_IDN(2))
    print ("--- channels ---")
    print (SIM.get_channel())
    print (SIM.set_channel(1))
    print (SIM.get_channel())
    print ("--- excitation ---")
    print (SIM.get_excitation())
    print (SIM.set_excitation(4))
    print (SIM.get_excitation())
    print ("--- range ---")
    print (SIM.get_excitation())
    print (SIM.set_excitation(4))
    print (SIM.get_excitation())
    print ("--- resistance ---")
    print (SIM.get_resistance())
    
    #SIM._close_connection()


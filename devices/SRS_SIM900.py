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
                gpib        = config[name]['gpib'],
                SIM921_port = config[name]['SIM921_port'],
                SIM925_port = config[name]['SIM925_port'],
                TIP_mode    = True)

    config[name]['device_ranges']       = SIM900.ranges
    config[name]['device_excitations']  = SIM900.excitations
    config[name]['device_integrations'] = SIM900.integrations
    return SIM

class SIM900(object):
    # Fixme:port
    def __init__(self,
                 name,
                 address = "",
                 delay = 0.1, 
                 gpib = "GPIB::1",
                 SIM921_port = 2,
                 SIM925_port = 1,
                 SIM928_port = 2,  # <- this is not implemented anymore (for now)
                 TIP_mode = False
                 ):
        
        self.SIM         = visa.instrument(gpib, ip = address, delay = delay, 
                                           instrument_delay= 0.05, term_char = "\r\n", eos_char = "\r\n")
        self.SIM921_port = SIM921_port
        self.SIM925_port = SIM925_port
        self.SIM928_port = SIM928_port

        self.TIP_mode = TIP_mode
        """
        TIP_mode  

        In TIP, the following sequence is carried out before a resistance measurement:
        ---
        self.backend.set_channel(     config[self.name]['device_channel'])
        self.backend.set_excitation(  config[self.name]['device_excitation'])
        self.backend.set_integration( config[self.name]['device_integration_time'])
        ---
        If one would reset the post-detection-filter each time, the settling time would be 3x as long. Thus, in TIP_mode, 
        the function 
        self.reset_post_detection_filter()
        is only executed in 
        self.set_integration()
        """


        """    
        exci={0:-1, 3:0, 10:1, 30:2, 100:3, 300:4, 1000:5, 3000:6, 10000:7, 30000:8}
        rang={0.02:0, 0.2:1, 2:2, 20:3, 200:4, 2000:5, 20000:6, 200000:7, 2000000:8, 20000000:9}
        tcon={0:-1, 0.3:0, 1:1, 3:2, 10:3, 30:4, 100:5, 300:6}

        """
        
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
        """
        self.ranges = {0:0.02, 1:0.2, 2:2, 3:20, 4:200, 5:2000, 6:20000, 7:200000, 8:2000000, 9:20000000}
        """
        self.excitations = [ # uV
                0, # excitation off
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
        """
        self.excitations = {-1:0, 0:3, 1:10, 2:30, 3:100, 4:300, 5:1000, 6:3000, 7:10000, 8:30000}

        """
        Filter timeconstants (TCON), settling time 7x longer
        self.integrations = [ # seconds
                #-1  -> filter off
                0.3, 
                1, 
                3, 
                10, 
                30, 
                100, 
                300
            ]
        """
        self.integrations = { -1:-1, 0:0.3, 1:1, 2:3, 3:10, 4:30, 5:100, 6:300}

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
        
        channel = int(self.get_value_from_SIM900(port,cmd))
        
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

        if channel == current_channel:
            logging.debug(f"Set (leave) channel at {channel}.")
            # do nothing
            pass
        else:
            logging.debug(f"Set channel to {channel}.")
            port  = self.SIM925_port
            cmd = f"CHAN {channel}"
            self.set_value_on_SIM900(port,cmd)

            if not self.TIP_mode:
                # wait for the SIM921 to settle ...
                self.reset_post_detection_filter()


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
        
        port  = self.SIM921_port
        cmd = "EXCI?"
        excitation = int (self.get_value_from_SIM900(port,cmd))
        logging.debug(f"Get excitation: {excitation} ({self.excitations[excitation]} uV).")
        
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
        
        current_excitation = self.get_excitation()

        if excitation == current_excitation:
            # do nothing
            port  = self.SIM921_port
            logging.debug(f"Set (leave) excitation to {excitation}.")
        else:
            port  = self.SIM921_port
            cmd = f"EXCI {excitation}"
            self.set_value_on_SIM900(port,cmd)
            logging.debug(f"Set excitation to {excitation}.")


            if not self.TIP_mode:
                # wait for the SIM921 to settle ...
                self.reset_post_detection_filter()
            
        
    
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
        
        port  = self.SIM921_port
        cmd = "RANG?"
        r_range = int (self.get_value_from_SIM900(port,cmd))

        logging.debug(f"Get range: {r_range} ({self.ranges[r_range]} Ohm).")
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

        current_r_range = self.get_range()
        if r_range == current_r_range:
            # do nothing
            return
        else:   
            port  = self.SIM921_port
            cmd = "RANG %i"%(r_range)
            self.set_value_on_SIM900(port,cmd)

            if not self.TIP_mode:
                # wait for the SIM921 to settle ...
                self.reset_post_detection_filter()

            logging.debug(f"Set range: {r_range} ({self.ranges[r_range]} Ohm).")
        
    
    def set_autogain(self):

        """
        Initiates the autogain cycle .

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        port  = self.SIM921_port
        cmd = "AGAI ON"
        self.set_value_on_SIM900(port,cmd)


        #
        # check weather the auto-gain cycle is complete
        cmd = "AGAI?"
        for i in range(15):
            time.sleep(1)
            again = int(self.get_value_from_SIM900(self.SIM921_port,cmd))
            print (again," ",i)
            if again == 0:
                break
            


   

    def get_integration(self):
        """
        Gets the integration time for the resistance measurement of the set channel.

        Parameters
        ----------
        None

        Returns
        -------
        integration: float
            Integration setting, that relates to the integration time .
        """

        cmd = "TCON?"
        port  = self.SIM921_port
        integration_setting = int (self.get_value_from_SIM900(port,cmd))
        logging.debug(f"Get integration setting : {integration_setting} ({self.integrations[integration_setting]*7} s)")
        return integration_setting

    def set_integration(self, integration):
        """
        Sets the integration time in seconds for the resistance measurement of the set channel.

        The filter time constant can be read using the TCON? query, and then indexing based on the returned value:
                TCON?   (Time Constant )    (Suggested MIN Settling Time)
                0             0.3 s                       2.1 s
                1             1 s                          7 s
                2             3 s                          21 s
                3             10 s                        70 s
                4             30 s                        210 s
                5             100 s                      700 s
                6             300 s                      2100 s  (35 minutes)

        Parameters
        ----------
        integration: float
            Integration that composes of integration time and those averages.

        Returns
        -------
        None
        """
        _integration_time_new = 0
        for integration_setting in range(len(self.integrations)):
            #print(f"in itteration: {integration_setting}")
            if integration >= self.integrations[integration_setting] * 7 :
                _integration_time_new  = self.integrations[integration_setting] * 7
            else:    
                break
        if integration_setting > 0:
            integration_setting -=1
        #print(f"Int filter settling time: {_integration_time_new}")
        #print(f"Int filter setting: {integration_setting} ({self.integrations[integration_setting]}s)")

        current_integration_time = self.get_integration()

        if current_integration_time == _integration_time_new:
            # do nothing
            logging.debug(f"Set (leave) integration setting to {integration_setting} ({self.integrations[integration_setting]*7} s).")
            return
        else:
            port  = self.SIM921_port
            cmd = f"TCON {integration_setting}"
            self.set_value_on_SIM900(port,cmd)
            logging.debug(f"Set integration setting to {integration_setting} ({self.integrations[integration_setting]*7} s).")
            
            if self.TIP_mode:
                # wait for the SIM921 to settle ...
                self.reset_post_detection_filter()
    
    
            

    def reset_post_detection_filter(self):
        """
        resets the post detection filter. Should be called after each change in channel, range, excitation

        The filter time constant can be read using the TCON? query, and then indexing based on the returned value:
                TCON?   (Time Constant )    (Suggested MIN Settling Time)
                0             0.3 s                       2.1 s
                1             1 s                          7 s
                2             3 s                          21 s
                3             10 s                        70 s
                4             30 s                        210 s
                5             100 s                      700 s
                6             300 s                      2100 s  (35 minutes)

        Parameters
        ----------
        None

        Returns
        -------
        None
        """        
        port  = self.SIM921_port
        cmd = "FRST"
        self.set_value_on_SIM900(port,cmd)

        current_integration_setting = self.get_integration()
        settling_time = self.integrations[current_integration_setting]*7
        time.sleep(settling_time)


    def get_resistance(self):
        """
        Gets the resistance value of the thermometer that is connected to the set channel.
        
        Note from Matt @ SRS Nov. 2022: 
        The RVAL? and PHAS? are subject to the Output Filter time constant -- 
        they do NOT ignore the filter. So, RVAL? results will have to settle if there is a sudden change to the applied resistance.
        RVAL? and PHAS? always return the averaged values.

        What the user probably wants to do, especially since they are multiplexing between different resistance values using an external SIM925, is something like this:

        [ configure the SIM925 to the desired channel to read ]
        [ connect the SIM900 mainframe to the SIM921 ]

        visa.write ('FRST')  // reset the post detection filter
        [ add a TIME DELAY, corresponding to 7* the filter time constant ]
        visa.write('RVAL?')
        res = visa.read()



        Parameters
        ----------
        None

        Returns
        -------
        resistance: float
            Resistance of the thermometer.
        """    
        
        port  = self.SIM921_port
        cmd = 'RVAL?'
        # not sure if we need this, quite clumsy:
        try:
            return float(self.get_value_from_SIM900(port,cmd))
        except ValueError as e:
            logging.debug (f"SIM921 error in get_resistance(): {e}")
            return 0
        
    def get_phase(self):
        """
        Gets the phase value of the thermometer.
        
        Note from Matt @ SRS Nov. 2022: 
        The RVAL? and PHAS? are subject to the Output Filter time constant -- 
        they do NOT ignore the filter. So, RVAL? results will have to settle if there is a sudden change to the applied resistance.
        RVAL? and PHAS? always return the averaged values.

        What the user probably wants to do, especially since they are multiplexing between different resistance values using an external SIM925, is something like this:

        [ configure the SIM925 to the desired channel to read ]
        [ connect the SIM900 mainframe to the SIM921 ]

        visa.write ('FRST')  // reset the post detection filter
        [ add a TIME DELAY, corresponding to 7* the filter time constant ]
        visa.write('RVAL?')
        res = visa.read()



        Parameters
        ----------
        None

        Returns
        -------
        resistance: float
            Resistance of the thermometer.
        """    
        
        port  = self.SIM921_port
        cmd = 'PHAS?'
        # not sure if we need this, quite clumsy:
        try:
            return float(self.get_value_from_SIM900(port,cmd))
        except ValueError as e:
            logging.debug (f"SIM921 error in get_phase(): {e}")
            return 0
        
        

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
        return self.get_value_from_SIM900_new(port,cmd)

    def get_value_from_SIM900_new(self,port,cmd):
        self.SIM_prolog(port)
        self.SIM.write(str(cmd))
        time.sleep(0.02)
        val = self.SIM.read()
        self.SIM_epilog()
        return val

    def get_value_from_SIM900_orig(self,port,cmd):
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
        self.SIM_prolog(port)
        self.SIM.write(str(cmd))
        self.SIM_epilog()

    
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

    format_str = "%(asctime)s %(levelname)-8s: %(message)s (%(filename)s:%(lineno)d)"
    logging.basicConfig(
        format=format_str,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    formatter = logging.Formatter(format_str)
    logger = logging.getLogger()
    #logger.setLevel(logging.DEBUG)

    SIM = SIM900("SIM900", address="10.22.197.15", gpib = "GPIB::1",  SIM921_port = 2, SIM925_port = 1, TIP_mode=True) 
    print ("--- *IDN? ---")
    print ("get IDN:1 ",SIM.get_IDN(1))
    print ("get IDN:2 ",SIM.get_IDN(2))
    
    print ("--- resistance ---")
    print ("get:R ",SIM.get_resistance())
    
    print ("--- channels ---")
    print ("set:2 ",SIM.set_channel(2))
    print ("get: ", SIM.get_channel())
    print ("set:1 ",SIM.set_channel(1))
    print ("get: ", SIM.get_channel())

    print ("--- excitation ---")
    print(SIM.excitations)
    print ("set:5 ",SIM.set_excitation(5))
    print ("get: ", SIM.get_excitation())
    print ("set:6 ",SIM.set_excitation(6))
    print ("get: ", SIM.get_excitation())

    print ("--- range ---")
    print (SIM.ranges)
    print ("set:6 ")
    SIM.set_range(6)
    print ("get: ", SIM.get_range())
    print ("set:5 ")
    SIM.set_range(5)
    print ("get: ", SIM.get_range())

    print ("--- autorange ---")
    print ("set autogain")
    SIM.set_autogain()
    #print ("get range ", SIM.get_range())
    #print ("get exci  ", SIM.get_excitation())


    print ("--- integration ---")
    print (SIM.integrations)
    print ("set: 5s ")
    SIM.set_integration(5)
    print ("get: ",   SIM.get_integration())
    print ("set: 11s ")
    SIM.set_integration(11)
    print ("get: ",   SIM.get_integration())

    for i in range(10):
        print ("get:R ",SIM.get_resistance())
        print ("get:P ",SIM.get_phase())



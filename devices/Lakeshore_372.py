# Lakeshore 372, Lakeshore 372 temperature controller driver
# Micha Wildermuth Micha.Wildermuth@kit.edu
# HR@KIT 
# largely rewritten for TIP 2019
# GPL



import logging
import time
#import devices.visa_prologix as visa
import serial


#from lib.tip_config import config


def driver(name):
    
    LS = Lakeshore_372(name,
                port    = config[name]['port'],
                delay   = config[name]['delay'],
                timeout = config[name]['timeout'])

    config[name]['device_ranges'] = LS.ranges
    config[name]['device_excitations'] = LS.excitations
    return LS


class Lakeshore_372(object):
    def __init__(self, name, port, delay=0.1, timeout = 1, **kwargs):

                
        self.serial_dev = serial.Serial()
        self.serial_dev.baudrate = 57600
        self.serial_dev.bytesize = serial.SEVENBITS
        self.serial_dev.stopbits = serial.STOPBITS_ONE
        self.serial_dev.parity   = serial.PARITY_ODD 
        self.serial_dev.port     = port
        self.serial_dev.open()

        
        #self._visa = ser
        # self._visa = visa.instrument(
        #     gpib, 
        #     ip = address, 
        #     delay = delay, 
        #     term_char = "\n",
        #     eos_char = "",
        #     timeout = timeout,
        #     instrument_delay = 0.06,
        #     debug = False
        #     )
            
        #
        #  a few default values
        #

        # static bridge conversion tables
        self._setup_bridge_tables()

        #
        # variables for the 'fast mode':
        # if integration is 0 then the channel settings are not being updated from the bridge
        # and the resistance asked directly
        # should only be used when scanning one thermometer
        self._channel = 0
        self._integration_time = 1

        self._excitation = 1
        self._excitation_mode = 1
        

        ''' heater '''
        self._heater_channel = 0
        self._heater_power = 0

        # maximal attempts for communication, before error is raised
        self._attempt_max = 4  
        #
        # reset the bridge and wait 5 seconds
        #
        self.write("*RST")
        time.sleep(3)
        #
        # Get the bridge version
        #
        self.idn =self.get_idn()
        #
        # Enable status reporing
        #
        self.write("*SRE 92")
        #
        # update the event status register to report all
        # here the bridge appears to be buggy
        #
        self.write("*ESE 220")
        #
        # disable autoscan
        #
        self._set_autoscan(False)
        self._autoscan = 0
        #
        # clear the message buffer
        #
        self.write("*CLS")
    
    def write(self,string):
        #print(string, flush = True)
        string+='\n'
        self.serial_dev.write(string.encode("ascii"))

    def read(self):
        readstr =  self.serial_dev.read_until()
        #print(readstr.strip().decode(),flush  = True)
        return (readstr.strip().decode()) 

    def ask(self,string):
        self.write(string)
        time.sleep(0.05)
        return self.read()

    def get_idn(self):
        """
        Gets the Instrument identification name of the device.

        Parameters
        ----------
        None

        Returns
        -------
        IDN: str
            Instrument identification name
        """
        # Corresponding command: <manufacturer>,<model>,<serial>,<date>[term] = *IDN?[term]
        logging.debug('Get IDN.')
        return self.ask('*IDN?')
        

    ####################################################################################################################
    ### bridge                                                                                                       ###
    ####################################################################################################################

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
        # Corresponding command: <channel>,<autoscan>[term] = SCAN?[term]
        channel, autoscan = self.ask("SCAN?").split(",")
        channel = int(channel)
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
        # Corresponding command: SCAN <channel>,<autoscan>[term]
        # INSET <channel>,<off/on>,<dwell>,<pause>,<curve number>,<tempco>[term]
        
        
        current_channel = self.get_channel()
        if current_channel == channel:
            # do nothing
            pass
        else:
            logging.debug('Set channel to {:d}.'.format(channel))
            self.write('SCAN {:d},{:d}'.format(channel, self._autoscan))
            self.write('*OPC')
            time.sleep(5)
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
        # Corresponding command: <mode>,<excitation>,<range>,<autorange>,<cs off>[term] = RDGRNG? <channel>[term]
        
        channel, mode, excitation, r_range, autorange, cs_off, autoscan = \
            self._get_channel_parameters()
        logging.debug('Get excitation of (current) channel {:d}: {:d} ({!s}).'
            .format(channel, excitation, self.excitation_ranges[excitation]))
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
        # Corresponding command: RDGRNG <channel>,<mode>,<excitation>,<range>,<autorange>,<cs off>[term]
        #keys, vals = zip(*self.excitation_ranges.items())
        #self._excitation = excitation #keys[np.argmax(np.array(vals) > excitation)-1]
        #cs_off = 0 # 0 = excitation on, 1 = excitation off (attention)

        channel, excitation_mode, current_excitation, r_range, autorange, cs_off, autoscan = \
            self._get_channel_parameters()

        if current_excitation == excitation:
            # do nothing
            return
        else:
            logging.debug('Set excitation of channel {!s} to {!s}.'
                .format(self._channel, excitation))
        
            self.write('RDGRNG {:d},{:d},{:d},{:d},{:d},{:d}'
                .format(channel, excitation_mode, excitation, r_range, autorange, cs_off))
            self.write('*OPC')
            time.sleep(3)
        
    
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
        channel, mode, excitation, r_range, autorange, cs_off, autoscan = \
            self._get_channel_parameters()
        logging.debug('Get range of (current) channel {:d}: {:d} ({!s}).'
            .format(channel, r_range,self.resistance_ranges[r_range]))
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
        # Corresponding command: RDGRNG <channel>,<mode>,<excitation>,<range>,<autorange>,<cs off>[term]
        channel, excitation_mode, excitation, current_r_range, autorange, cs_off, autoscan = \
            self._get_channel_parameters()

        if r_range == -1:  # autorange
            autorange = 1
            self.write('RDGRNG {:d},{:d},{:d},{:d},{:d},{:d}'
                .format(channel, excitation_mode, excitation, r_range, autorange, cs_off))
            self.write('*OPC')
            time.sleep(3)

        elif r_range == current_r_range:
            # do nothing
            return
        else:
            logging.debug('Set range of channel {:d} to {:d} ({!s}).'
            .format(channel, r_range,self.resistance_ranges[r_range]))
            self.write('RDGRNG {:d},{:d},{:d},{:d},{:d},{:d}'
                .format(channel, excitation_mode, excitation, r_range, autorange, cs_off))
            self.write('*OPC')
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
        if self._integration_time  > 1 :
            
            channel = self.get_channel()
            time.sleep(0.1)

            for i in range(10):
                # query the event status register, with 000 the bridge should be settled enough
                ESR = int(self.ask("*ESR?"))
                if int(ESR):
                    time.sleep(1)
                else:
                    break
            # the ESR register was not cleared ... return nothing sensful
            if i == 9: return 0

            # Corresponding command: <ohm value>[term] = RDGR? <channel>[term]
            logging.debug('Get resistance of channel {:d}.'.format(channel))
            resistance = float(self.ask('RDGR? {:d}'.format(channel)))
        else:
            # 'fast mode'
            logging.debug('Get resistance of channel {:d}.'.format(self._channel))
            resistance = float(self.ask('RDGR? {:d}'.format(self._channel)))

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
        # Corresponding command: FILTER <channel>,<off/on>,<settle time>,<window>[term]

        channel = self.get_channel()
        status, settle_time, window = self._get_filter(channel)
        logging.debug('Settling time from bridge: %f'%(settle_time))
        if integration < 1:
            integration = 1

        if settle_time == integration:
            # do nothing
            return
        else:
            self._set_filter(channel,settle_time=integration)
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
            self._integration = int(str(self._ask('FILTER? {:d}'.format(self._channel))).split(sep=',')[1])
            return self._integration
        except Exception as err:
            logging.error('Cannot get integration. Return last value instead. {!s}'.format(err))
            return self._integration

    def _get_autoscan(self):
        channel, autoscan = self.ask("SCAN?").split(",")
        return bool(int(autoscan))

    def _set_autoscan(self,status = False):

        channel, autoscan = self.ask("SCAN?").split(",")

        self.write('SCAN {:d},{:d}'.format(int(channel), int(status)))
        

    def _get_channel_parameters(self):
        # get channel parameters for comparison
        
        # query channel first
        channel, autoscan = self.ask("SCAN?").split(",")

        # and then the parameter
        mode, excitation, r_range, autorange, cs_off = \
            self.ask("RDGRNG? %s"%(channel)).split(",")
        # where 
        # mode [0: voltage excitation | 1:current excitation]
        # autorange [0: off | 1: on]
        # cs_off [0: excitation on | 1: excitation off]


        # and input scan parameters (unused)
        #onoff, dwell, pause, curveno, tempco = \
        #    self.ask("INSET? %s"%(channel)).split(",")
        # where
        # ...

        return (int(channel), int(mode), int(excitation), int(r_range),
             int(autorange), int(cs_off), int(autoscan))
    
    def _set_channel_parameters(self):
        pass


    def _get_status_byte(self,channel):
        #channel = self.get_channel()
        return (self.ask("RDGST? %s"%(channel)))

    def _get_filter(self,channel):
        status, settle_time, window = \
        self.ask('FILTER? {:d}'.format(channel)).split(',')
        return bool(int(status)), int(settle_time), int(window)

    def _set_filter(self, channel, status = True, settle_time = 5, window = 2 ):

        if self._get_filter(channel) != (status, settle_time, window):
            self.write('FILTER %d,%d,%d,%d'%(channel,int(status), settle_time, window))
            self.write('*OPC')
            time.sleep(settle_time)


        
        

    ####################################################################################################################
    ### heater                                                                                                       ###
    ####################################################################################################################

    def set_heater_channel(self, channel):
        """
        Sets the channel that is used to supply the heater.

        Parameters
        ----------
        channel: int
            Number of channel that is connected to the heater.

        Returns
        -------
        None
        """
        self._heater_channel = channel
        logging.debug('Set heater channel to {!s}.'.format(channel))

    def get_heater_channel(self):
        """
        Gets the channel that is used to supply the heater.

        Parameters
        ----------
        None

        Returns
        -------
        channel: int
            Number of channel that is connected to the heater.
        """
        logging.debug('Get heater channel.')
        return self._heater_channel

    def set_heater_power(self, power):
        """
        Sets the heat power of the set channel.

        Parameters
        ----------
        power: float
            Heat power.

        Returns
        -------
        None
        """
        try:
            self._heater_power = power
            self._write('MOUT {:.8f}'.format(self._heater_power)) # TODO: Do we need to care about the range?
            logging.debug('Set heater power to {!s}.'.format(power))
        except ValueError as e:
            raise ValueError('Cannot set manual heater power to {!s}.\n{:s}'.format(power, e))

    def set_heater_range(self, range):
        self._write('HTRRNG {:d}'.format(range))

    def get_heater_power(self):
        """
        Gets the heat power of the set channel.

        Parameters
        ----------
        None

        Returns
        -------
        power: float
            Heat power.
        """
        # Corresponding command: HTR? HTRRNG?, MOUT?
        try:
            logging.debug('Get heater power.')
            return float(self._ask('MOUT?'))
            #return float(self._ask('HTR?'))
        except Exception as err:
            logging.error('Cannot get heater power. Return last value instead. {!s}'.format(err))
            return self._heater_power

    def set_local(self):
        """
        Sets to local mode.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # Corresponding command: MODE <mode>[term]
        mode = 0  # <mode> 0 = local, 1 = remote, 2 = remote with local lockout.
        self._write('MODE {:d}'.format(mode))

    def _close(self):
        """
        Closes the connection.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        visa._close_connection()




    def _setup_bridge_tables(self):

        self.ranges = [
            'None',
            '2 mOhm',
            '6.32 mOhm',
            '20 mOhm',
            '63.2 mOhm',
            '200 mOhm',
            '632 mOhm',
            '2 Ohm',
            '6.32 Ohm',
            '20 Ohm',
            '63.2 Ohm',
            '200 Ohm',
            '632 Ohm',
            '2 kOhm',
            '6.32 kOhm',
            '20 kOhm',
            '63.2 kOhm',
            '200 kOhm',
            '632 kOhm',
            '2 MOhm',
            '6.32 MOhm',
            '20 MOhm',
            '63.2 MOhm'
        ]

        self.excitations = [
            'None',
            '2 uV or 1 pA',
            '6.32 uV or 3.16 pA',
            '20 uV or 10 pA',
            '63.2 uV or 31.6 pA',
            '200 uV or 100 pA',
            '632 uV or 316 pA',
            '2 mV or 1 nA',
            '6.32 mV or 3.16 nA',
            '20 mV or 10 nA',
            '63.2 mV or 31.6 nA',
            '200 mV or 100 nA',
            '632 mV or 316nA',
            '1 uA',
            '3.16 uA',
            '10 uA',
            '31.6 uA',
            '100 uA',
            '316 uA',
            '1 mA',
            '3,16 mA',
            '10 mA',
            '31.6 mA'
        ]

        self.resistance_ranges = {
            1: 2e-3, # '2 mOhm'
            2: 6.32e-3, # '6.32 mOhm',
            3: 20e-3, # '20 mOhm',
            4: 63.2e-3, # '63.2 mOhm',
            5: 200e-3, # '200 mOhm',
            6: 632e-3, # '632 mOhm',
            7: 2, # '2 Ohm',
            8: 6.32, # '6.32 Ohm',
            9: 20, # '20 Ohm',
            10: 63.2, # '63.2 Ohm',
            11: 200, # '200 Ohm',
            12: 632, # '632 Ohm',
            13: 2e3, # '2 kOhm',
            14: 6.32e3, # '6.32 kOhm',
            15: 20e3, # '20 kOhm',
            16: 63.2e3, # '63.2 kOhm',
            17: 200e3, # '200 kOhm',
            18: 632e3, # '632 kOhm',
            19: 2e6, # '2 MOhm',
            20: 6.32e6, # '6.32 MOhm',
            21: 20e6, # '20 MOhm',
            22: 63.2e6, # '63.2 MOhm'
            }

        self.excitation_ranges = {
            1: (2e-6, 1e-12), # '2 uV or 1 pA',
            2: (6.32e-6, 3.16e-12), # '6.32 uV or 3.16 pA',
            3: (20e-6, 10e-12), # '20 uV or 10 pA',
            4: (63.2e-6, 31.6e-12), # '63.2 uV or 31.6 pA',
            5: (200e-6, 100e-12), # '200 uV or 100 pA',
            6: (632e-6, 316e-12), # '632 uV or 316 pA',
            7: (2e-3, 1e-9), # '2 mV or 1 nA',
            8: (6.32e-3, 3.16e-9), # '6.32 mV or 3.16 nA',
            9: (20e-3, 10e-9), # '20 mV or 10 nA',
            10: (63.2e-3, 31.6e-9), # '63.2 mV or 31.6 nA',
            11: (200e-3, 100e-9), # '200 mV or 100 nA',
            12: (632e-3, 316e-9), # '632 mV or 316nA',
            13: (None, 1e-6), # '1 uA',
            14: (None, 3.16e-6), # '3.16 uA',
            15: (None, 10e-6), # '10 uA',
            16: (None, 31.6e-6), # '31.6 uA',
            17: (None, 100e-6), # '100 uA',
            18: (None, 316e-6), # '316 uA',
            19: (None, 1e-3), # '1 mA',
            20: (None, 3.16e-3), # '3,16 mA',
            21: (None, 10e-3), # '10 mA',
            22: (None, 31.6e-3), # '31.6 mA'
            }

        self._reading_ccr = {
            0: 'CS OVL',
            1: 'VCM OVL',
            2: 'VMIX OVL',
            3: 'VDIF OVL',
            4: 'R. OVER',
            5: 'R. UNDER',
            6: 'T. OVER',
            7: 'T. UNDER'
        }

        self._heater_ranges = {
            0: False, # 'off',
            1: 31.6e-6, # '31.6 uA',
            2: 100e-6, # '100 uA',
            3: 316e-6, # '316 uA',
            4: 1e-3, # '1 mA',
            5: 3.16e-3, # '3.16 mA',
            6: 10e-3, # '10 mA',
            7: 31.6e-3, # '31.6 mA',
            8: 100e-3, # '100 mA'
        }




if __name__ == "__main__":
    print ("debug start")


    LS=Lakeshore_372("LS372", "COM3")
    
    scan_mode = True
    fast_mode = False
    print("IDN: %s"%(LS.idn))
    if scan_mode :
        for loop in range(3):
            print ("loop %d"%(loop))
            for ch in [1,2,5,6]:
                print("Channel: %d"%(ch))
                LS.set_channel(ch)
                LS.set_range(10)
                LS.set_excitation(4)
                LS.set_integration(10)
                tm=time.time()
                for i in range(5):
                    print (LS.get_resistance())
                print (time.time()-tm)

    if fast_mode:
        ch = 0
        LS.set_channel(ch)
        LS.set_excitation(4)
        LS.set_range(10)
        LS.set_integration(0)
        tm=time.time()
        for i in range(10):
            print (LS.get_resistance(),flush = True)
        print (time.time()-tm)
        

""" 
                     model == 'Lakeshore 372AC':     
                        while :
                            settled = self.askAndLog('RDGSTL?')
                            settledMeasure1 = int(settled.split(',')[1].strip())
                            if settledMeasure0 == 0 and settledMeasure1 == 0:
                                break
                            settledMeasure0 = settledMeasure1
                            self.wait(0.05)

"""




"""
    def reset(self):
        self.__write('*RST')
        sleep(.5)
       
    def get_common_mode_reduction(self):
        ans = self.__ask('CMR?')
        return bool(int(ans))
        
    def get_guard_drive(self):
        ans = self.__ask('GUARD?')
        return bool(int(ans))
        
    def get_Temp(self, channel):
        try:
            ans = float(self.__ask('RDGK? %s' % channel))
        except ValueError:
            print "LS: get_res value error, try again"
            ans = float(self.__ask('RDGK? %s' % channel))
        return ans
        
    def get_Res(self, channel):
        try:
            ans = self.__ask('RDGR? %s' % channel)
            #print "#%s#" % (ans)
            return float(ans)
        except ValueError:
            print "LS: get_res value error, try again"
            ans = self.__ask('RDGR? %s' % channel)
            #print "#%s#" % (ans)
            return float(ans)

        
    def get_resistance_range(self, channel):
        ans = self.__ask('RDGRNG? %s' % channel)
        return int(ans.split(',')[2])
        
    def get_excitation_mode(self, channel):
        ans = self.__ask('RDGRNG? %s' % channel)
        return int(ans.split(',')[0])
        
    def get_excitation_range(self, channel):
        ans = self.__ask('RDGRNG? %s' % channel)
        return int(ans.split(',')[1])
        
    def get_autorange(self, channel):
        ans = self.__ask('RDGRNG? %s' % channel)
        return bool(int(ans.split(',')[3]))
        
    def get_excitation_on(self, channel):
        ans = self.__ask('RDGRNG? %s' % channel)
        return (int(ans.split(',')[4]) == 0)
        
    def get_scanner_dwell_time(self, channel):
        ans = self.__ask('INSET? %s' % channel)
        return float(ans.split(',')[1])
        
    def get_scanner_pause_time(self, channel):
        ans = self.__ask('INSET? %s' % channel)
        return float(ans.split(',')[2])
        
    def get_filter_on(self, channel):
        ans = self.__ask('FILTER? %s' % channel)
        return bool(int(ans.split(',')[0]))
        
    def get_filter_settle_time(self, channel):
        ans = self.__ask('FILTER? %s' % channel)
        return float(ans.split(',')[1])
        
    def set_filter_settle_time(self, val, channel):
        cmd = 'FILTER %s,1,%d,80' % (channel,int(np.round(val)))
        self.__write(cmd)
        getattr(self, 'get_filter_settle_time%s' % channel)()
        getattr(self, 'get_filter_on%s' % channel)()
        getattr(self, 'get_filter_reset_threshold%s' % channel)()
        
    def get_heater_range(self):
        ans = self.__ask('HTRRNG?')
        return int(ans)
        
    def get_heater_power(self):
        ans = self.__ask('HTR?')
        return float(ans)
        
    def set_heater_range(self, val):
        self.__write('HTRRNG %d' % val)
        self.get_heater_range()
        
    def get_heater_status(self):
        ans = self.__ask('HTRST?')
        return ans
        
    def get_mode(self):
        ans = self.__ask('MODE?')
        return int(ans)

    def set_mode(self, mode):
        self.__write('MODE %d' % mode)
        self.get_mode()

    def set_local(self):
        self.set_mode(1)

    def set_remote(self):
        self.set_mode(2)
        
    def get_temperature_control_mode(self):
        ans = self.__ask('CMODE?')
        return int(ans)

    def set_temperature_control_mode(self, mode):
        setp = self.get_temperature_control_setpoint()

        self.__write('CMODE %d' % mode)
        self.get_temperature_control_mode()

        new_setp = self.get_temperature_control_setpoint()
        if new_setp != setp:
          logging.info('setpoint changed from %g to %g when changing CMODE to %s. Setting it back...' % (setp, new_setp, mode))
          self.set_temperature_control_setpoint(setp)

    def get_temperature_control_pid(self):
        ans = self.__ask('PID?')
        fields = ans.split(',')
        if len(fields) != 3:
            return None
        fields = [float(f) for f in fields]
        return fields

    def set_temperature_control_pid(self, val):
        assert len(val) == 3, 'PID parameter must be a triple of numbers.'
        assert val[0] >= 0.001 and val[0] < 1000, 'P out of range.'
        assert val[1] >= 0 and val[1] < 10000, 'I out of range.'
        assert val[2] >= 0 and val[2] < 2500, 'D out of range.'
        cmd = 'PID %.5g,%.5g,%.5g' % (val[0], val[1], val[2])
        self.__write(cmd)
        self.get_temperature_control_pid()

    def get_still_heater(self):
        ans = self.__ask('STILL?')
        return float(ans)

    def set_still_heater(self, val):
        self.__write('STILL %.2F' % (val))

    def get_temperature_control_setpoint(self):
        ans = self.__ask('SETP?')
        return float(ans)
        
    def set_temperature_control_setpoint(self, val):
        for attempts in range(5):
          self.__write('SETP %.3E' % (val))
          setp = self.get_temperature_control_setpoint()
          if np.abs(setp - val) < 1e-5: return # all is well
          logging.warn('Failed to change setpoint to %g (instead got %g). Retrying...' % (val, setp))
          sleep(5.)
        logging.warn('Final attempt to change setpoint to %g failed (instead got %g).' % (val, setp))
        
    def get_temperature_control_channel(self):
        ans = self.__ask('CSET?')
        return int(ans.split(',')[0])
        
    def get_temperature_control_use_filtered_reading(self):
        ans = self.__ask('CSET?')
        return bool(ans.split(',')[1])
        
    def get_temperature_control_setpoint_units(self):
        ans = self.__ask('CSET?')
        return ans.split(',')[2]
        
    def get_temperature_control_heater_max_range(self):
        ans = self.__ask('CSET?')
        return int(ans.split(',')[5])
        
    def get_temperature_control_heater_load_resistance(self):
        ans = self.__ask('CSET?')
        return float(ans.split(',')[6])

    
    """
        
        
            


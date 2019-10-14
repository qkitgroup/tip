# Lakeshore 370, Lakeshore 370 temperature controller driver
# Micha Wildermuth Micha.Wildermuth@kit.edu
# stripped down and adapted for TIP 2019
# Based on Joonas Govenius <joonas.govenius@aalto.fi>, 2014
# Based on Lakeshore 340 driver by Reinier Heeres <reinier@heeres.eu>, 2010.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import visa_prologix as visa
import logging
import time
import numpy as np
import random


class driver(object):
    def __init__(self, name, ip, gpib=8, delay=0.3, **kwargs):
        self._visa = visa.instrument(gpib, ip=ip, delay=delay, **kwargs)
        self._attempt_max = 4  # maximal attempts for communication, before error is raised
        self._resistance = None
        ''' channel '''
        self._channel = None
        self._autoscan = False
        # TODO: turn all channels off
        ''' excitation '''
        self._excitation = None
        self._excitation_mode = 1
        self._range = None
        self._autorange = None
        ''' averaging '''
        self._integration = None
        ''' heater '''
        self._heater_channel = None
        self._heater_power = None
        
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

    def _ask(self, cmd):
        attempt = 0
        while attempt < self._attempt_max:
            try:
                return self._visa.ask(cmd)
            except:
                logging.debug('Attempt #%d to communicate with LakeShore failed.', attempt + 1)
                time.sleep((1 + attempt) ** 2 * (0.1 + np.random.rand()))
                attempt += 1
        raise

    def _write(self, cmd):
        attempt = 0
        while attempt < self._attempt_max:
            try:
                return self._visa.write(cmd)
            except:
                logging.debug('Attempt #%d to communicate with LakeShore failed.', attempt + 1)
                time.sleep((1 + attempt) ** 2 * (0.1 + np.random.rand()))
                attempt += 1
        raise

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
        try:
            logging.debug('Get IDN.')
            return str(self._ask('*IDN?'))
        except Exception  as e:
            return 'Lakeshore'

    ####################################################################################################################
    ### bridge                                                                                                       ###
    ####################################################################################################################

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
        try:
            self._channel = channel
            self._write('SCAN {:d},{:d}'.format(channel, int(self._autoscan)))
            logging.debug('Set channel to {!s}.'.format(self._channel))
        except ValueError as e:
            raise ValueError('Cannot set channel to {!s}.\n{:s}'.format(channel, e))

    def get_channel(self):
        """
        Gets the channel that is used to measure the resistance of the thermometer.

        Parameters
        ----------
        None

        Returns
        -------
        channel: int
            Number of channel that is connected to the thermometer.
        """
        # Corresponding command: <channel>,<autoscan>[term] = SCAN?[term]
        try:
            logging.debug('Get channel.')
            return int(str(self._ask('SCAN?')).split(sep=',')[0])
        except Exception as err:
            logging.error('Cannot get channel. Return last value instead. {!s}'.format(err))
            return self._channel

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
        try:
            keys, vals = zip(*self.excitation_ranges.items())
            self._excitation = keys[np.argmax(np.array(vals) > excitation)-1]
            cs_off = 0 # 0 = excitation on, 1 = excitation off (attention)
            self._write('RDGRNG {:d},{:d},{:f},{:f},{:d},{:d}'.format(self._channel, self._excitation_mode, self._excitation, self._range, self._autorange, cs_off))
            logging.debug('Set excitation of channel {!s} to {!s}.'.format(self._channel, excitation))
        except ValueError as e:
            raise ValueError('Cannot set excitation of channel {!s} to {!s}.\n{:s}'.format(self._channel, excitation, e))

    def get_excitation(self):
        """
        Gets the excitation value of the set channel.

        Parameters
        ----------
        None

        Returns
        -------
        val: float
            Excitation value of the bias with which the resistance of the thermometer is measured.
        """
        # Corresponding command: <mode>,<excitation>,<range>,<autorange>,<cs off>[term] = RDGRNG? <channel>[term]
        try:
            logging.debug('Get excitation of channel {!s}.'.format(self._channel))
            ans = str(self._ask('RDGRNG?')).split(sep=',')
            return self.excitation_ranges[ans[1]][ans[0]]
        except Exception as err:
            logging.error('Cannot get channel. Return last value instead. {!s}'.format(err))
            return self._excitation

    def set_range(self, range):
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
        try:
            if range == -1:  # autorange
                self._autorange = True
            else:
                self._autorange = False
                keys, vals = zip(*self.resistance_ranges.items())
                self._range = keys[np.argmax(np.array(vals).T[self._excitation_mode] > range)]
            cs_off = 0  # 0 = excitation on, 1 = excitation off (attention)
            self._write('RDGRNG {:d},{:d},{:f},{:f},{:d},{:d}'.format(self._channel, self._excitation_mode, self._excitation, self._range, self._autorange, cs_off))
            logging.debug('Set range of channel {!s} to {!s}.'.format(self._channel, range))
        except ValueError as e:
            raise ValueError('Cannot set range of channel {!s} to {!s}.\n{:s}'.format(self._channel, range, e))

    def get_range(self):
        """
        Gets the resistance measurement range of the set channel.

        Parameters
        ----------
        None

        Returns
        -------
        range: float
            Resistance measurement range for the thermometer.
        """
        # Corresponding command: <mode>,<excitation>,<range>,<autorange>,<cs off>[term] = RDGRNG? <channel>[term]
        try:
            logging.debug('Get range of channel {!s}.'.format(self._channel))
            ans = str(self._ask('RDGRNG?')).split(sep=',')
            if ans[3]:
                return -1
            else:
                return self.resistance_ranges[ans[2]]
        except Exception as err:
            logging.error('Cannot get range. Return last value instead. {!s}'.format(err))
            return self._range

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
        # Corresponding command: <ohm value>[term] = RDGR? <channel>[term]
        # Corresponding command: <status bit weighting>[term] = RDGST? <channel> [term]
        try:
            logging.debug('Get resistance of channel {!s}.'.format(self._channel))
            self._resistance = float(self._ask('RDGR? {:d}'.format(self._channel)))
        except Exception as err:
            logging.error('Cannot get channel. Return last value instead. {!s}'.format(err))
        return self._resistance

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
        try:
            self._integration = np.round(integration)
            status = int(bool(integration))
            window = 80
            self._write('FILTER {:d},{:d},{:d},{:d}'.format(self._channel, status, self._integration, window))
            logging.debug('Set integration of channel {!s} to {!s}.'.format(self._channel, integration))
        except ValueError as e:
            raise ValueError('Cannot set integration of channel {!s} to {!s}.\n{:s}'.format(self._channel, integration, e))

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
            return int(str(self._ask('FILTER? {:d}'.format(self._channel))).split(sep=',')[1])
        except Exception as err:
            logging.error('Cannot get integration. Return last value instead. {!s}'.format(err))
            return self._integration

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

    """
    def reset(self):
        self.__write('*RST')
        sleep(.5)

    def __ask(self, msg):
        attempt = 0
        while True:
          try:
            m = self._visa.ask("%s" % msg).replace('\r','')
            sleep(.01)
            break
          except:
            if attempt >= 0: logging.warn('Attempt #%d to communicate with LakeShore failed.', 1+attempt)
            if attempt < 4:
              sleep((1+attempt)**2 * (0.1 + random.random()))
            else:
              raise
        return m

    def __write(self, msg):
        attempt = 0
        while True:
          try:
            self._visa.write("%s" % msg)
            sleep(.5)
            break
          except:
            if attempt > 0: logging.warn('Attempt #%d to communicate with LakeShore failed.', 1+attempt)
            if attempt < 4:
              sleep((1+attempt)**2 * (0.1 + random.random()))
            else:
              raise

 

    def _get_IDN(self):
        return self.__ask('*IDN?')
        
    def get_common_mode_reduction(self):
        ans = self.__ask('CMR?')
        return bool(int(ans))
        
    def get_guard_drive(self):
        ans = self.__ask('GUARD?')
        return bool(int(ans))
        
    def get_scanner_auto(self):
        ans = self.__ask('SCAN?')
        return bool(int(ans.split(',')[1]))

    def set_scanner_auto(self, val):
        ch = self.get_scanner_channel()
        cmd = 'SCAN %d,%d' % (ch, 1 if val else 0)
        self.__write(cmd)
        self.get_scanner_auto()
        self.get_scanner_channel()
        
    def get_scanner_channel(self):
        ans = self.__ask('SCAN?')
        return int(ans.split(',')[0])

    def set_scanner_channel(self, val):
        auto = self.get_scanner_auto()
        cmd = 'SCAN %d,%d' % (val, 1 if auto else 0)
        self.__write(cmd)
        self.get_scanner_auto()
        self.get_scanner_channel()

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
        
    def get_filter_reset_threshold(self, channel):
        ans = self.__ask('FILTER? %s' % channel)
        return float(ans.split(',')[2])
        
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

    # functions added for TIP
    def _get_Channel(self):
        return self.get_scanner_channel()
    def _set_Channel(self,channel):
        self.channel = channel
        return self.set_scanner_channel(channel)
        
    def _get_ave(self):
        # just a proxy in the moment
        return self.get_Res(self.channel)
        
    def get_T(self):
        return self.get_Temp(self.channel)
        
    def get_Rval(self):
        return self.get_Res(self.channel)
        
    def set_output0(self,OUT_Volt): # HEATER interface
            return self.set_Voltage(OUT_Volt)

    def set_Voltage(self,OUT_Volt): # HEATER interface
            return self.set_Voltage(OUT_Volt)
            
    def set_Heat(self,power):
        self.__write('MOUT %.8F' % (power))
    def get_Heat(self):
        return float(self.__ask('MOUT?'))
    def get_Range(self): 
        return self.get_resistance_range(self.channel)
    def get_Excitation(self):
        return get_excitation_range(self.channel)
    def get_Channel(self): 
        return self._get_Channel()
    def setup_device(self): 
        pass
    """
        
        
            
if __name__ == "__main__":
    LS=Lakeshore_370("LS370")
    #print LS._get_IDN()
    #print LS._set_Channel(8)
    print LS._get_Channel()
    #print LS.get_Rval()
    #print LS._get_ave()
    print LS.get_T()
    
    print LS.set_Heat(1e-7)
    print LS.get_Heat()
    print LS.set_Heat(0)
    print LS.get_Heat()


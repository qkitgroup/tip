# Lakeshore 370, Lakeshore 370 temperature controller driver
# Hannes Rotzinger hannes.rotzinger@kit.edu 
# stript down and adapted for TIP 2015
# Base code 
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
#import visa
import logging
from time import sleep
import numpy as np
import random


class Lakeshore_370(object):
    def __init__(self,
                 name,
                 ip="129.13.93.80",
                 gpib="GPIB::12",
                 delay = 0.1,
                   reset=False, 
                   **kwargs
               ):
                
        self._visa = visa.instrument(gpib,ip=ip,delay=delay)
        
        self._channels = kwargs.get('channels', (1, 2, 5, 6, 7, 8))
        #self.set_scanner_channel
        self.channel = self._get_Channel()
        
        self.R_format_map = {
            1: '2 mOhm',
            2: '6.32 mOhm',
            3: '20 mOhm',
            4: '63.2 mOhm',
            5: '200 mOhm',
            6: '632 mOhm',
            7: '2 Ohm',
            8: '6.32 Ohm',
            9: '20 Ohm',
            10: '63.2 Ohm',
            11: '200 Ohm',
            12: '632 Ohm',
            13: '2 kOhm',
            14: '6.32 kOhm',
            15: '20 kOhm',
            16: '63.2 kOhm',
            17: '200 kOhm',
            18: '632 kOhm',
            19: '2 MOhm',
            20: '6.32 MOhm',
            21: '20 MOhm',
            22: '63.2 MOhm'
            }

        self.Exe_format_map = {
            1: '2 uV or 1 pA',
            2: '6.32 uV or 3.16 pA',
            3: '20 uV or 10 pA',
            4: '63.2 uV or 31.6 pA',
            5: '200 uV or 100 pA',
            6: '632 uV or 316 pA',
            7: '2 mV or 1 nA',
            8: '6.32 mV or 3.16 nA',
            9: '20 mV or 10 nA',
            10: '63.2 mV or 31.6 nA',
            11: '200 mV or 100 nA',
            12: '632 mV or 316nA',
            13: '1 uA',
            14: '3.16 uA',
            15: '10 uA',
            16: '31.6 uA',
            17: '100 uA',
            18: '316 uA',
            19: '1 mA',
            20: '3,16 mA',
            21: '10 mA',
            22: '31.6 mA'
            }


        self._heater_ranges = {
            0: 'off',
            1: '31.6 uA',
            2: '100 uA',
            3: '316 uA',
            4: '1 mA',
            5: '3.16 mA',
            6: '10 mA',
            7: '31.6 mA',
            8: '100 mA' }

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


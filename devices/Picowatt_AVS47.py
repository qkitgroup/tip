# Picowatt_AVS47 class, to perform the communication between the Wrapper and the device
# Hannes Rotzinger hannes.rotzinger@kit.edu 2010- 2019 for TIP 
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
import types
import time
import logging


class driver(object):
    '''
    This is the python driver for the Picowatt AVS 47
    resistance bridge
    '''


    def __init__(self, name, address, gpib="GPIB::20", delay=0,**kwargs):
        '''
        Initializes the AVS_47, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false

        Output:
            None
        '''
        
        self._address = address
        self.debug = kwargs.get('debug',False)
        
        self._visainstrument = visa.instrument(
            gpib, 
            ip = address, 
            delay = delay, 
            term_char = "\r",
            eos_char = "\r",
            timeout = 1,
            instrument_delay = 0,
            debug = self.debug
            )
        self.averages = 0
        self.setup_device()

    def setup_device(self,reset=False):
        if reset:
            # give the device a power on reset
            self._visainstrument.write("*RST")
        
            # give the controller a power on reset
            self._visainstrument.write("ponrst")
        
            time.sleep(6)
        
        # put the AVS into the input mode
        self._set_input(1)
        # Make the system remote
        self._visainstrument.write("REM 1")
        
        self._visainstrument.write("*ESE 1")
        # connect the MAV bit to the SRQ
        self._visainstrument.write("*SRE 32")

        # unset the message return header
        self._set_no_header()

        # issue the operation complete flag
        self._visainstrument.write("*OPC")
        
    
    def get_idn(self):
        return self._visainstrument._get_idn()
        
    def get_resistance(self):
        if self.averages > 0:
            # the time to get the AVS settled after averaging can vary a lot.
            #
            #self._visainstrument.write("*ESE 1") 
            #self._visainstrument.write("*SRE 32")
            
            #self._visainstrument.write("*OPC")   
            self._visainstrument.write("*CLS")
            self._visainstrument.write("ADC; AVE %d; AVE?"%(self.averages))
            #self._visainstrument.write("AVE " + str(self.averages))
            #time.sleep(float(self.averages*0.4+1))
            #self._visainstrument.write("AVE ?")
            #self._visainstrument.wait_for_srq()
            #print dir(self._visainstrument)
            #time.sleep(1)
            self._get_message_available()
            #print( int(self._visainstrument._get_spoll().rstrip()))

            return self._visainstrument.read()
        else:
            self._visainstrument.write("ADC")
            time.sleep(1)
            self._visainstrument.write("RES ?")
            #        self._visainstrument.wait_for_srq()
            #print dir(self._visainstrument)
            #time.sleep(1)
            #print int(self._visainstrument._get_spoll().rstrip())
            return self._visainstrument.read().split()[1]
    



    def get_channel(self):
        return int(self._visainstrument.ask("MUX ?",instrument_delay=1))

    def set_channel(self,channel):
        # change the mux to channel n
        cmd="MUX " + str(channel)
        self._visainstrument.write(cmd)
        time.sleep(1)
        return self.get_channel()

    def get_excitation(self):
        return int(self._visainstrument.ask("EXC ?",instrument_delay=1))

    def set_excitation(self,excitation):
        # change the excitation
        cmd="EXC " + str(excitation)
        self._visainstrument.write(cmd)
        return self.get_excitation()

    def get_range(self):
        return int(self._visainstrument.ask("RAN ?",instrument_delay=1))

    def set_range(self,n):
        if n==10:
            cmd="ARN 1"
        else:
            self._visainstrument.write("ARN 0")
            cmd="RAN " + str(int(n))
        self._visainstrument.write(cmd)
        time.sleep(3)
        return self.get_range()

    def set_integration(self,time):
        # The AVS needs 0.4 seconds per average so:
        # time seconds  are int(time/0.4) avages
        self.averages = int(time/0.4)
        
    def set_remote(self):
        self._visainstrument.write("REM 1")
        
    def set_local(self):
        self._visainstrument.write("REM 0")

    def close(self):
        # Put the controller back in zero (shorted) inputs
        #self._visainstrument.write("INP 0")
        # local the controller
        self._visainstrument.write("REM 0")

 
        

    

    def reset(self):
        '''
        Resets the instrument to default values
        The AVS47 is a litte strange here, this might not work like expected

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')
        time.sleep(0.5)
        self.get_all()


    def _get_message_available(self):
        #
        # MAV: poll for message available on the GPIB bus
        # *OPC, *ESR 1, SRE 32 should be set
        # should be used between send and recv
        max_iter  = 100
        for i in range(max_iter):
            MAV = self._visainstrument._get_spoll()
            if self.debug:
                print(MAV)
            if MAV:
                try:
                    if (int(MAV) == 16):
                        print(i)
                        break
                except ValueError:
                    pass
            time.sleep(0.3)
    
    def _set_no_header(self):
        self._visainstrument.write("HDR 0")

    # communication with device
           
    def _get_remote(self):
        return self._visainstrument.ask("REM ?")
    def _get_overload(self):
        return self._visainstrument.ask("OVL ?")
    
    def _set_input(self,n):
        cmd="INP " + str(n)
        self._visainstrument.write(cmd)

    def _get_input(self):
        return int(self._visainstrument.ask("INP ?"))
    
    def _set_autorange(self,ON=1):
        cmd = "ARN "+str(ON)
        self._visainstrument.write(cmd)
    def _get_autorange(self):
        return int(self._visainstrument.ask("ARN ?"))

    def _get_delay(self, channel):
        '''
        Reads the pulse delay from the specified channel

        Input:
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            delay (float) : delay in seconds
        '''
        logging.debug(__name__ + ' : get delay for channel %d' % channel)
        

    def _set_delay(self, val, channel):
        '''
        Sets the delay of the pulse of the specified channel

        Input:
            val (float)   : delay in seconds
            channel (int) : 1 or 2, the number of the designated channel

        Output:
            None
        '''
        logging.debug(__name__ + ' : set delay for channel %d to %f' % (channel, val))


# do some checking ...
if __name__ == "__main__":
    #10.22.197.62
    avs=driver(  "AVS47_1",
        address = "10.22.197.63",
        gpib    = "GPIB::20",
        timeout = 1,
        delay   = 0.2,
        debug   = False)
    #time.sleep(5)
    #avs._visainstrument.write("*CLS")
    
    #print (avs.get_idn())
    #print (avs.get_range())
    #print (avs.get_channel())
    #print (avs.get_excitation())
    for c in [0,1,2]:
        avs.set_integration(2)
        print (avs.set_channel(c))
        print (avs.set_excitation(4))
        print (avs.set_range(10))
        print (float(avs.get_resistance()))
    ##print dir(avs)
    #avs.reset()
    #avs._open()
    #avs.set_remote()
    
    #print avs._get_autorange()
    #avs._set_autorange(ON=0)
    #
    #avs._set_channel(0,4,7)
    #print avs._get_mux()
   
    #print avs._get_adc()
    
    #print avs._get_range()
    #print avs._get_id()
    
    #print avs._get_resistance()
    #print (avs.set_range(0))

    #print(avs._get_ave())
    #savs._close()
    
    #avs.set_local()

"""
AVS 47  Number codes
modes={
INPUT_ZERO=0,
INPUT_MEASURE=1,
INPUT_REFERENCE=2
}

channels={
CH0=0,
CH1=1,
CH2=2,
CH3=3,
CH4=4,
CH5=5,
CH6=6,
CH7=7
}

ranges={
RANGE_NONE=0,
RANGE_2R=1,
RANGE_20R=2,
RANGE_200R=3,
RANGE_2K=4,
RANGE_20K=5,
RANGE_200K=6,
RANGE_2M=7
}
excitations={
EXC_NONE=0,
EXC_3_uV=1,
EXC_10_uV=2,
EXC_30_uV=3,
EXC_100_uV=4,
EXC_300_uV=5,
EXC_1_mV=6,
EXC_3_mV=7
}

measure={
DISPLAY_R=0,
DISPLAY_dR=1,
DISPLAY_ADJ_REF=2,
DISPLAY_REF=3,
DISPLAY_EXC=4,
DISPLAY_530_HEATER_VOLTAGE=5,
DISPLAY_530_HEATER_CURRENT=6,
DISPLAY_530_SET_POINT=7
}
"""


"""
    def _request_resistance(self):

        # Clear the status byte
        self._visainstrument.write("*CLS")

        # connect the MAV bit to the SRQ
        self._visainstrument.write("*ESE 1;*SRE 32")
        time.sleep(1)
        # Get the next ADC conversion into the controllers buffer
        self._visainstrument.write("ADC;")
        # wait one ADC conversion (0.4s)
        time.sleep(0.5)
        # initiate the reading
        #self._visainstrument.write("RES ?; *OPC")
        self._visainstrument.write("RES ?")
        #operation complete
        # this will set the MAV bit when done
        #self._visainstrument.write("*OPC")
    def _request_ave_resistance(self):

        # Clear the status byte
        self._visainstrument.write("*CLS")

        # connect the MAV bit to the SRQ
        self._visainstrument.write("*ESE 1;*SRE 32")
        #time.sleep(1)
        # Get the next ADC conversion into the controllers buffer
        self._visainstrument.write("ADC;")
        self._visainstrument.write("AVE 2")
        # wait one ADC conversion (0.4s each)
        time.sleep(1)
        # initiate the reading
        #self._visainstrument.write("RES ?; *OPC")
        #self._visainstrument.write("RES ?")
        self._visainstrument.write("AVE ?")
        i=0
        while(not int(self._get_overload())):
            i+=1

            if i>20:
                print "AVS47 claims an overload"
                break
            
        #operation complete
        # this will set the MAV bit when done
        #self._visainstrument.write("*OPC")
        
    def _get_resistance(self):
        #self._request_resistance()
        self._request_ave_resistance()
        # int sleep_time_ms=500
        #time.sleep(1)
        if self._message_available():
            # the answer probably has to be converted to something useful
            return float(self._visainstrument.read().split()[1])
    """
"""
    def _unset_Header(self):
        self._visainstrument.write("HDR 0")

    def _message_available(self):
        for i in range(20):
            spr=int(self._visainstrument._get_spoll().rstrip())
            # print "serial poll:",spr," #",i
            if (spr & 16)==16:
                #print float(self._visainstrument.read().split()[1])
                return True
            time.sleep(0.4)
        return False
        """

"""   
        int avs47::is_message_available(void)
        {
        unsigned char status_byte

        # do a serial poll of the bridge
        status_byte=serial_poll()

        unsigned char mav

        mav=status_byte & 0x10

        mav = mav >> 4

        #ifdef AVS47_DEBUG
        #printf("\n Serial poll=0x%04X",status_byte)

        std::cout << "\n Serial poll: " << gsd::str::pretty_print_as_binary(status_byte)
        std::cout.flush()

        #printf("\n Serial poll=0x%04X",status_byte)

        # RVE's custom device status
        printf("\n Device Status=0x%04X",status_byte& 15)

        printf("\n MAV = %d",mav)
        fflush(stdout)
        #endif

        # check for both RSQ and message waiting (see p. 25 in
        # RV electronica AVS47-IB manual
        #        if (status_byte == 0x50)

        return mav

        }
        """


"""
        double avs47::get_numeric_response(void)
        response_str = this->read_response_if_message_available()
        if (response_str.size()==0)
        return value
        
        # first 4 chars are text garbage
        #        response_str=response_str.substr(4,response_str.size())
        # split on *single* whitespace
        gsd::str::split(response_str,words, ' ')
        gsd::str::string_to_val(words[1],value)
        return value
        """


"""
    def _set_channel(self,channel, excitation, range):
        
        ZERO = 0
        MEASURE=1

        #Change the input to zero
        cmd="INP " + str(ZERO)
        self._visainstrument.write(cmd)
    
        # change the mux to channel n
        cmd="MUX " + str(channel)
        self._visainstrument.write(cmd)
    
        # change the excitation
        cmd="EXC " + str(excitation)
        self._visainstrument.write(cmd)
    
        # change the range, 10 means autorange
        #if range == 10:
        #cmd="ARN 1"
        #else:
        cmd="ARN 0"
        self._visainstrument.write(cmd)
    
        cmd="RAN " + str(range)
        self._visainstrument.write(cmd)
    
        # change the input to measure
        cmd="INP " + str(MEASURE)
        self._visainstrument.write(cmd)
        
        # the AVS needs some time to get settled.
        # change the input to measure
        cmd="DLY 15"
        self._visainstrument.write(cmd)
        time.sleep(15)
"""
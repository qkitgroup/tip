#!/usr/bin/env python

"""
Dummy heater driver / basic interface
"""
import sys
import random
import time
import numpy as np
import logging

import pyvisa as visa


class driver(object):
    def __init__(self, name):
        self._channel = 1
        self.resistance = 120
        self.setup_device()
        pass

    def setup_device(self):
        pass

    def get_idn(self):
        return "Keysight B2900 as heater."

    def get_heater_power(self):

        return (self.V) ** 2 / self.resistance

    def set_heater_power(self, value):
        max_value = 10
        if value < 0:
            value = 0
        if value > max_value:
            value = max_value

        self.V = np.sqrt(value * self.resistance)
        logging.info("applied heater voltage: %f" % (self.V))
        set_bias_value(self.V, channel=self._channel)

    def get_heater_channel(self):
        return 0

    def set_heater_channel(self, value):
        pass

    def set_local(self):
        pass

    def close(self):
        pass

    def set_bias_value(self, value, channel=1):
        """ "
        Sets bias value of channel <channel> to value <val>.
        Parameters
        ----------
        val: float
            Bias value.
        channel: int
            Number of channel of interest. Must be 1 for SMUs with only one
            channel and 1 or 2 for SMUs with two channels. Default is 1.
        Returns
        -------
        None
        """
        # Corresponding Command: [:SOUR[c]]:VOLT: voltage
        # Corresponding Command: :DISPlay:VIEW mode
        try:
            logging.debug(
                "{!s}: Set bias value{:s} to {:g}".format(
                    __name__, self._log_chans[_channels][channel], val
                )
            )
            self._write(
                ":sour{:s}:{:s}:lev {:g}".format(
                    self._cmd_chans[_channels][channel], 1, val
                )
            )  # necessary to cast as scientific float! (otherwise only >= 1e-6 possible)
            self._write(":disp:view sing{:d}".format(channel))
        except Exception as e:
            logging.error(
                "{!s}: Cannot set bias value{:s} to {!s}".format(
                    __name__, self._log_chans[_channels][channel], val
                )
            )
            raise type(e)(
                "{!s}: Cannot set bias value{:s} to {!s}\n{!s}".format(
                    __name__, self._log_chans[_channels][channel], val, e
                )
            )
        return

    def _write(self, cmd):
        """
        sends a visa command <cmd>, waits until "operation complete" and raises eventual errors of the device.
        parameters
        ----------
        cmd: str
            command that is send to the instrument via pyvisa and ni-visa backend.
        returns
        -------
        none
        """
        self._visainstrument.write(cmd)
        while not bool(int(self._visainstrument.query("*OPC?"))):
            time.sleep(1e-6)
        self._raise_error()
        return

    def _ask(self, cmd):
        """
        sends a visa command <cmd>, waits until "operation complete", raises eventual errors of the device and returns the read answer <ans>.
        parameters
        ----------
        cmd: str
            command that is send to the instrument via pyvisa and ni-visa backend.
        returns
        -------
        answer: str
            answer that is returned at query after the sent <cmd>.
        """
        if "?" in cmd:
            ans = self._visainstrument.query(cmd).rstrip()
        else:
            ans = self._visainstrument.query("{:s}?".format(cmd)).rstrip()
        while not bool(int(self._visainstrument.query("*opc?"))):
            time.sleep(1e-6)
        self._raise_error()
        return ans

    def _raise_error(self):
        """
        Gets errors of instrument and as the case may be raises a python error.
        Parameters
        ----------
        None
        Returns
        -------
        None
        """
        errors = self.get_error()
        if len(errors) == 1 and errors[0][0] == 0:  # no error
            return
        else:
            msg = __name__ + " raises the following errors:"
            for err in errors:
                msg += "\n{:s} ({:s})".format(self.err_msg[err[0]], err[1])
            raise ValueError(msg)

    def get_error(self):
        """
        Gets errors of instrument and removes them from the error queue.
        Parameters
        ----------
        None
        Returns
        -------
        err: array of str
            Entries from the error queue
        """
        # Corresponding Command: :SYSTem:ERRor:ALL?
        # :SYSTem:ERRor:CODE:ALL?
        # :SYSTem:ERRor:CODE[:NEXT]?
        # :SYSTem:ERRor:COUNt?
        # :SYSTem:ERRor[:NEXT]?
        try:
            logging.debug("{!s}: Get errors of instrument".format(__name__))
            err = [self._visainstrument.query(":syst:err:all?").rstrip().split(",", 1)]
            err = [[int(float(e[0])), str(e[1])] for e in err]
            if not err:
                err = [[0, "no error", 0]]
            return err
        except Exception as e:
            logging.error("{!s}: Cannot get errors of instrument".format(__name__))
            raise type(e)(
                "{!s}: Cannot get errors of instrument\n{!s}".format(__name__, e)
            )


if __name__ == "__main__":

    ht = driver("Keysight_B2900")
    ht.set_heater_power(1e-2)
    print(ht.get_heat())

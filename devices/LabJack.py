#!/usr/bin/env python
# Labjack class for U3 type of labjack devices (USB)
import u3


class LabJack(object):

    def __init__(self):
        # first establish device connection

        try:
            self.dev=u3.U3()
            self.dev.ping()
            
        except:
            raise 
    # some helpers, modbus variables/ see wwwsite http://labjack.com/support/labjackpython
    def set_output0(self,value):
        return self.dev.writeRegister(5000,value)
    def set_output1(self,value):
        return self.dev.writeRegister(5002,value)
    def get_input0(self):
        return self.dev.readRegister(0)
    def get_input1(self):
        return self.dev.readRegister(2)
    def get_input2(self):
        return self.dev.readRegister(4)
    def get_input3(self):
        return self.dev.readRegister(6)


if __name__ == "__main__":
    LJ = LabJack()
    print LJ.set_output0(1.1)
    print LJ.set_output1(1.1)
    print LJ.get_input0()
    print LJ.get_input1()
    print LJ.get_input2()
    print LJ.get_input3()

# pidcontrol for TIP  version 0.3 written by HR@KIT 2011 - 2019
#
# changelog:
# 0.3 code cleanup for TIP 2.0

from lib.tip_config import config, _types_dict

class pidcontrol(object):
    def __init__(self,name):
        self.name = name

        config[self.name]['control_error'] = 0
        _types_dict['control_error'] = float

        self.dState = 0 # Last position input
        self.iState = 0 # Integrator state
        
        self.iMax  = 0.1  # Maximum allowable integrator state
        self.iMin  = -0.001  # Minimum allowable integrator state
 
    def get_new_heat_value(self,measured_Temperature):
        error = config[self.name]['control_temperature'] - measured_Temperature
        config[self.name]['control_error'] = error
        return self.updatePID(error,measured_Temperature)
        
    def updatePID(self,error,reading):
        "PID algorithm "
        pTerm = 0
        dTerm = 0
        iTerm = 0
        #calculate the proportional term
        pTerm = config[self.name]['control_p'] * error
        
        #calculate the integral state with appropriate limiting
        self.iState += error
        if self.iState > self.iMax:
            self.iState = self.iMax
        if self.iState < self.iMin:
            self.iState = self.iMin
        
        iTerm = config[self.name]['control_i'] * self.iState  #calculate the integral term
        dTerm = config[self.name]['control_d'] * ( reading - self.dState)
        self.dState = reading
        print( "P:%.5f I:%.5f D:%.5f terms"%(pTerm,iTerm,dTerm))
        print( "I:%.5f D:%.5f states"%(self.iState,self.dState))
        return pTerm + iTerm - dTerm

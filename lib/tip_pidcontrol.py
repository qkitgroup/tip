# pidcontrol for TIP  version 0.2 written by HR@KIT 2011
#
# TODO (urgent) make everything thread safe.

class pidcontrol(object):
    def __init__(self,data):
        
	self.data = data
        self.hold = False
        
        self.target_temperature = 0.01
        
        #P = data.ctrl_pid[0]  # 0.00004  # proportional gain
        #I = data.ctrl_pid[1]  # 0.00004  integral gain
        #D = data.ctrl_pid[2]  # 0.00001 derivative gain

        self.dState = 0 # Last position input
        self.iState = 0 # Integrator state
        
        self.iMax  = 0  # Maximum allowable integrator state
        self.iMin  = 0  # Minimum allowable integrator state

    def set_P(self, P):
        self.data.ctrl_PID[0] = P
    def set_I(self,I):
        self.data.ctrl_PID[1] = I
    def set_D(self,D):
        self.data.ctrl_PID[2] = D
    def set_hold(self,state=False):
        self.hold = state
        
    def set_target_temperature(self,T_set):
        self.target_temperature = T_set
        
    def update_Rate(self,measured_rate):
        error = self.target_temperature-measured_rate
        return self.updatePID(error,measured_rate)

    def update_Heat(self,measured_Temperature):
        error = self.data.get_ctrl_Temp()-measured_Temperature
        return self.updatePID(error,measured_Temperature),error
        
    def updatePID(self,error,reading):
        "PID algorithm "
        pTerm = 0
        dTerm = 0
        iTerm = 0
        #calculate the proportional term
        pTerm = self.data.get_PID()[0] * error
        
        #calculate the integral state with appropriate limiting
        self.iState += error
        if self.iState > self.iMax:
            self.iState = self.iMax
        if self.iState < self.iMin:
            self.iState = self.iMin
            
        iTerm = self.data.get_PID()[1] * self.iState; #calculate the integral term
        dTerm = self.data.get_PID()[2] * ( reading - self.dState)
        self.dState = reading
        return pTerm + iTerm - dTerm

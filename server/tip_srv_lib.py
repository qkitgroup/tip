from tip_data import DATA as data
success = "1"
fail    = "0"

def parse_request(reqest):
    """ This method parses the request sting 
        and returns a result string 
        Syntax:
        The general syntax is

        'CMD'/'SUB CMD'/'Z'/'ZZ'/...
        where 
        'CMD' can be the command:
        GET as in [G|g|GET|get|Get|gET|GEt|geT]
        SET as in [S|s|SET|set|Set|sET|SEt|seT]

        VERSION as in [V|VERSION]
            -> returns the version of TIP

        EXIT as in [E|EXIT]
            -> sends an exit request to the server (quit) 

        'SUB CMD' can be the subcommand:
        TCTRL as in [TCTRL]
            
            -> in the set mode:
            The temperature control has the following structure:
            SET/TCTRL/CHANNEL/PARAMETER/VALUE
            CHANNEL is the named channel given in the config file
            if CHANNEL is ommitted ('//') then the default channel is assumed
            
            SET/TCTRL/-CHANNEL-/T/-value-      -> sets the target temperature
            SET/TCTRL/-CHANNEL-/HDEV/-value-   -> sets the target heater given in the config file
            SET/TCTRL/-CHANNEL-/P/-value-      -> sets the P value 
            SET/TCTRL/-CHANNEL-/I/-value-      -> sets the I value
            SET/TCTRL/-CHANNEL-/D/-value-      -> sets the D value
            
            -> in the get mode:
            GET/TCTRL/CHANNEL/PARAMETER
            CHANNEL is the named channel given in the config file
            if CHANNEL is ommitted ('//') then the default channel is assumed
            GET/TCTRL/-CHANNEL-/T              -> returns the target temperature
            GET/TCTRL/-CHANNEL-/HDEV           -> returns the target heater
            GET/TCTRL/-CHANNEL-/P              -> returns the target P
            GET/TCTRL/-CHANNEL-/I              -> returns the target I
            GET/TCTRL/-CHANNEL-/D              -> returns the target D

        THERM as in [T|cis(THERM)] # cis = case in-sensitive: 

            GET/SETS THERMOMETER specific values:
            where CHANNEL is a named channel given in the config file

            SET/TERM/-CHANNEL-/E
            SET/TERM/-CHANNEL-/R

            GET/TERM/-CHANNEL-/T
            GET/TERM/-CHANNEL-/R
    """
    "tokenize the request string"
    cmds = cmd.upper().split("/")
    "remove heading or trailing white spaces"
    cmds = [cmd.strip() for cmd in cmds]

    cmd = cmds.pop(0)
    if 'G' in  cmd[0] or 'GET' in cmd:
        return get_handler(cmds)
    elif 'S' in cmd[0] or 'SET' in cmd:
        return set_handler(cmds)
    elif 'V' in cmd[0] or 'VERSION' in cmd:
        return version_handler(cmds)
    elif cmd == "0":
        return debug_handler(cmds)
    elif 'EXIT' in cmd:
        return exit_handler(cmds)
    else:
        return invalid_syntax_handler(cmd,cmds)


def set_handler(cmds):
    logstr(cmds)
    try:
        cmd = cmds.pop(0)
    except IndexError:
        return "Error: No subcommand given!"
    if "TCTRL" in cmd:
        return tctrl_set_handler(cmds)
    elif 'T' in cmd[0] or "THERM" in cmd:
        return therm_set_handler(cmds)
    else:
        return "Error: Subcommand not recognized! "+cmd


		
def get_handler(cmds):
    "/GET/CMD"
    logstr(cmds)
    try:
        cmd = cmds.pop(0)
    except IndexError:
        return "Error: No subcommand given!"
    if "TCTRL" in cmd:
        return tctrl_get_handler(cmds)
    elif 'T' in cmd[0] or "THERM" in cmd:
        return therm_get_handler(cmds)
    else:
        return "Error: Subcommand not recognized! "+cmd

	
			
			elif "THERMOMETER".find(cmds[1]) == 0:
				if cmds[2] == "":
					term = self.data.bridge.Control_Channel.channel
				elif cmds[2] == ":":
					term = -1
				else:
					try:
						term = int(cmds[2])
					except ValueError:
						self.wo(' '.join('%i'%T.channel for T in self.data.bridge.channels)) # return all available channels
						return
				try: sub_cmd = cmds[3]
				except IndexError: sub_cmd = "TEMP"  #DEFAULT
				if sub_cmd == "": sub_cmd = "TEMP"
				
				if "TEMPERATURE".find(sub_cmd) == 0:
					try:
						if "HISTORY".find(cmds[3]) == 0:
							if term == -1:	self.wo(pickle.dumps([T.get_Temp() for T in self.data.bridge.channels]))
							else:			self.wo(pickle.dumps(self.data.bridge.channels[self.data.bridge.chmap[term]].get_Temp() ))		
							return
					finally:					
						if term == -1:		self.wo(' '.join(["%f"%T.get_last_Temp() for T in self.data.bridge.channels]))
						else:				
							self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_last_Temp())
							print(self.data.bridge.channels[self.data.bridge.chmap[term]].get_last_Temp())
				elif "ALL".find(sub_cmd) == 0:
					if term == -1:			self.wo(pickle.dumps([T.get_all() for T in self.data.bridge.channels]))
					else:					self.wo(pickle.dumps(self.data.bridge.channels[self.data.bridge.chmap[term]].get_all()))
				elif "AGE".find(sub_cmd) == 0:
					try:
						if "HISTORY".find(cmds[3]) == 0:
							if term == -1:	self.wo(pickle.dumps([time.time()-T.get_timestamps() for T in self.data.bridge.channels]))
							else:			self.wo(pickle.dumps(time.time()-self.data.bridge.channels[self.data.bridge.chmap[term]].get_timestamps() ))		
							return
					finally:					
						if term == -1:		self.wo(' '.join(["%f"%T.get_age() for T in self.data.bridge.channels]))
						else:				self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_age() )
				elif "TIME".find(sub_cmd) == 0:
					try:
						if "HISTORY".find(cmds[3]) == 0:
							if term == -1:	self.wo(pickle.dumps([T.get_timestamps() for T in self.data.bridge.channels]))
							else:			self.wo(pickle.dumps(self.data.bridge.channels[self.data.bridge.chmap[term]].get_timestamps() ))		
							return
					finally:					
						if term == -1:		self.wo(' '.join(["%f"%T.get_timestamps()[-1] for T in self.data.bridge.channels]))
						else:				self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_timestamps()[-1] )
				elif "RANGE".find(sub_cmd) == 0:
					if term == -1:		self.wo(' '.join(["%i"%T.get_Range() for T in self.data.bridge.channels]))
					else:				self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_Range() )
				elif "EXCITATION".find(sub_cmd) == 0:
					if term == -1:		self.wo(' '.join(["%i"%T.get_Excitation() for T in self.data.bridge.channels]))
					else:				self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_Excitation() )
				else:
					self.wo("Sub command after GET/TEMPERATURE/? not known...")
					return

			else:
					pass
		except Exception as e:
			print ("get_handler exception..." + str(e))
			#raise e

def exit_handler(cmds):
    reply = "tip is going down\n"
    data.set_wants_abort()
    wants_abort = True

def debug_handler(cmds):
    return cmds
    #cur_thread = threading.currentThread()
    #response = "%s: %s" % (cur_thread.getName(), data)
    #self.wo(response)
der version_handler(cmds):
    return str(2)

def invalid_syntax_handler(cmd,cmds):
    reply = cmd + " " + cmds+ ":\n Invalid syntax, either 'set/...' or 'get/...'\n"

def tctrl_set_handler(cmds):
    "/TCTRL/-channel-/-value-"
    try:
        chan = cmds.pop(0)
    except IndexError:
        return "Error TCTRL: No CHANNEL given!"
    try:
        cmd = cmds.pop(0)
    except IndexError:
        return "Error TCTRL: No PARAMETER given!"
    try:
        value = cmds.pop(0)
    except IndexError:
        return "Error TCTRL: No VALUE given!"
    try: 
        if   'T' in cmd[0]:
            return data.set_ctrl_Temp(float(value))
        elif 'HDEV' in cmd:
            return data.set_ctrl_heater_device(value)
        elif 'P' in cmd[0]:
            return self.data.set_P(float(value))
        elif 'I' in cmd[0]:
            return self.data.set_I(float(value))
        elif 'D' in cmd[0]:
            return self.data.set_D(float(value))
        else:
            return "Error TCTRL: Parameter not recognized! "+cmd
    except ValueError as e:
        #.....
        raise e

def tctrl_get_handler(cmds)

    "/TCTRL/-channel-/-value-"
    try:
        chan = cmds.pop(0)
    except IndexError:
        return "Error TCTRL: No CHANNEL given!"
    try:
        cmd = cmds.pop(0)
    except IndexError:
        return "Error TCTRL: No PARAMETER given!"
    try: 
        if   'T' in cmd[0]:
            return str(data.get_ctrl_Temp())
        elif 'HDEV' in cmd:
            return data.set_ctrl_heater_device(value)
        elif 'P' in cmd[0]:
            return str(data.get_PID()[0]))
        elif 'I' in cmd[0]:
            return str(data.get_PID()[1]))
        elif 'D' in cmd[0]:
            return str(data.get_PID()[2]))
        elif 'H' in cmd[0] or 'HEAT' in cmd:
            return str(data.get_last_Heat()[0])
        elif 'E' in cmd[0] or 'ERROR' in cmd:
            return str(data.get_last_pidE()[0])
        elif 'A' in cmd[0] or 'ALL' in cmd:
            #print(json.dumps([T.get_Temp() for T in self.data.bridge.channels]))				
			#self.wo(pickle.dumps(self.data.get_all_pid()))
            return ""
        else:
            return "Error TCTRL: Parameter not recognized! "+cmd
    except ValueError as e:
        #.....
        raise e
    

def therm_set_handler(cmds):
    " handles Thermometer request  
    "/THERM/-channel-/-param-/-value-"
    try:
        chan = cmds.pop(0)
    except IndexError:
        return "Error THERM: No CHANNEL given!"
    try:
        cmd = cmds.pop(0)
    except IndexError:
        return "Error THERM: No PARAMETER given!"
    try:
        value = cmds.pop(0)
    except IndexError:
        return "Error THERM: No VALUE given!"
    try:
        if "" in chan:
            term = self.data.bridge.Control_Channel.channel
        elif ":" in chan:
            return "Channel wildcard ':' not allowed in set mode."
        elif chan in [list_of_thermomenters]
            therm = chan 
        else:
            return "Thermometer "+chan+" not found or no active thermometer"
    except Exception as e:
        print(e)
        return "Thermometer "+chan+" not found or no active thermometer"

        try:
            if 'R' in cmd[0] or 'RANGE' in cmd:
                # FIXME: this syntax is going to change 
                self.data.bridge.channels[self.data.bridge.chmap[term]].set_Range(int(value))
                return success
            elif 'E' in cmd[0] or 'EXCITATION' in cmd:
                # FIXME: this syntax is going to change 
                self.data.bridge.channels[self.data.bridge.chmap[term]].set_Excitation(int(value))
                return success
            else:
				return "Only Range and Excitation are settable in SET/THERMOMETER/X/. Set Control Temp with SET/TCTRL/-CHANNEL-/"
        except ValueError:
					return "Please specify Range or Excitation as integer value."


def therm_get_handler(cmds):

    " handles Thermometer request  
    "/THERM/-channel-/-param-/"
    try:
        chan = cmds.pop(0)
    except IndexError:
        return "Error THERM: No CHANNEL given!"
    try:
        cmd = cmds.pop(0)
    except IndexError:
        return "Error THERM: No PARAMETER given!"
        
    try:
        if "" in chan:
            term = self.data.bridge.Control_Channel.channel
        elif ":" in chan:
            return "Channel wildcard ':' not allowed in set mode."
        elif chan in [list_of_thermomenters]
            therm = chan 
        else:
            return "Thermometer "+chan+" not found or no active thermometer"
    except Exception as e:
        print(e)
        return "Thermometer "+chan+" not found or no active thermometer"

        try:

    		elif "THERMOMETER".find(cmds[1]) == 0:
				if cmds[2] == "":
					term = self.data.bridge.Control_Channel.channel
				elif cmds[2] == ":":
					term = -1
				else:
					try:
						term = int(cmds[2])
					except ValueError:
						self.wo(' '.join('%i'%T.channel for T in self.data.bridge.channels)) # return all available channels
						return
				try: sub_cmd = cmds[3]
				except IndexError: sub_cmd = "TEMP"  #DEFAULT
				if sub_cmd == "": sub_cmd = "TEMP"
				
				if "TEMPERATURE".find(sub_cmd) == 0:
					try:
						if "HISTORY".find(cmds[3]) == 0:
							if term == -1:	self.wo(pickle.dumps([T.get_Temp() for T in self.data.bridge.channels]))
							else:			self.wo(pickle.dumps(self.data.bridge.channels[self.data.bridge.chmap[term]].get_Temp() ))		
							return
					finally:					
						if term == -1:		self.wo(' '.join(["%f"%T.get_last_Temp() for T in self.data.bridge.channels]))
						else:				
							self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_last_Temp())
							print(self.data.bridge.channels[self.data.bridge.chmap[term]].get_last_Temp())
				elif "ALL".find(sub_cmd) == 0:
					if term == -1:			self.wo(pickle.dumps([T.get_all() for T in self.data.bridge.channels]))
					else:					self.wo(pickle.dumps(self.data.bridge.channels[self.data.bridge.chmap[term]].get_all()))
				elif "AGE".find(sub_cmd) == 0:
					try:
						if "HISTORY".find(cmds[3]) == 0:
							if term == -1:	self.wo(pickle.dumps([time.time()-T.get_timestamps() for T in self.data.bridge.channels]))
							else:			self.wo(pickle.dumps(time.time()-self.data.bridge.channels[self.data.bridge.chmap[term]].get_timestamps() ))		
							return
					finally:					
						if term == -1:		self.wo(' '.join(["%f"%T.get_age() for T in self.data.bridge.channels]))
						else:				self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_age() )
				elif "TIME".find(sub_cmd) == 0:
					try:
						if "HISTORY".find(cmds[3]) == 0:
							if term == -1:	self.wo(pickle.dumps([T.get_timestamps() for T in self.data.bridge.channels]))
							else:			self.wo(pickle.dumps(self.data.bridge.channels[self.data.bridge.chmap[term]].get_timestamps() ))		
							return
					finally:					
						if term == -1:		self.wo(' '.join(["%f"%T.get_timestamps()[-1] for T in self.data.bridge.channels]))
						else:				self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_timestamps()[-1] )
				elif "RANGE".find(sub_cmd) == 0:
					if term == -1:		self.wo(' '.join(["%i"%T.get_Range() for T in self.data.bridge.channels]))
					else:				self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_Range() )
				elif "EXCITATION".find(sub_cmd) == 0:
					if term == -1:		self.wo(' '.join(["%i"%T.get_Excitation() for T in self.data.bridge.channels]))
					else:				self.wo(self.data.bridge.channels[self.data.bridge.chmap[term]].get_Excitation() )
				else:
					self.wo("Sub command after GET/TEMPERATURE/? not known...")
					return

			else:
					pass
		except Exception as e:
			print ("get_handler exception..." + str(e))
			#raise e
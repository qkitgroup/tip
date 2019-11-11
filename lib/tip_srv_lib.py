#
# This file mainly handles external requests
# rewritten from scratch for TIP 2.0 HR@KIT 2019
#
import sys
import logging
import json

from lib.tip_config import config, convert_string_to_value


def parse_request(request):
    """ This method parses the request sting 
        and returns a result string 
        Syntax:
        The general syntax is (case insensitive)

        'CMD'/'SUB CMD'/'Z'/'ZZ'/...
        where 
        'CMD' can be the command:
        GET as in [G|g|GET|get|Get|gET|GEt|geT]
        SET as in [S|s|SET|set|Set|sET|SEt|seT]

        VERSION as in [V|VERSION]
            -> returns the version of TIP

        CONFIG  as in [C]CONFIG]
        EXIT as in [E|EXIT]
            -> sends an exit request to the server (quit) 

        We directly modify the dynamical config with params
        'SUB CMD' can be the subcommand:
            -> in the set mode:
            The temperature control has the following structure:
            SET/INSTRUMENT/PARAMETER/VALUE
            CHANNEL is the named channel given in the config file
            if CHANNEL is ommitted ('//') then the default channel is assumed
    """
    "tokenize the request string"
    logging.info(request)

    cmds = request.strip('/').split("/")
    "remove heading or trailing white spaces"
    cmds = [cmd.strip() for cmd in cmds]
    cmd = cmds.pop(0).lower()

    if 'g' in  cmd[0] or 'get' in cmd:
        return get_handler(cmds)
    elif 's' in cmd[0] or 'set' in cmd:
        return set_handler(cmds)
    elif 'v' in cmd[0] or 'version' in cmd:
        return (config['system']['version'])
    elif 'c' in cmd[0] or 'config' in cmd:
        return(json.dumps(config,indent=2,sort_keys=True))
    elif 'm' in cmd[0] or 'macro' in cmd:
        return ""
    elif 'exit' in cmd:
        return exit_handler(config)
    else:
        return ("invalid syntax : "+request)



def get_handler(cmds):
    "/GET/[instrument|device]/"
    try:
        cmd = cmds.pop(0) # case sensitive 'instruments'
    except IndexError:
        return "Error: No instrument or device given!"
    except Exception as e:
        print ("get_handler exception..." + str(e))
        raise (e)
    if cmd in config.keys():
        return (get_param_handler(config[cmd],cmds))
    elif '' == cmd:
        return ("Error: Subcommand not recognized! "+cmd)
    elif '::' in cmd[:2]:
        return config.dump_json()
    elif ':' in cmd[0]:
        return json.dumps(list(config.keys()))
    else:
        return ("Error: Subcommand not recognized! "+cmd)

    
def set_handler(cmds):
    "/set/[instrument|device]"
    try:
        cmd = cmds.pop(0)
    except IndexError:
        return "Error: No instrument or device given!"
    except Exception as e:
        print ("set_handler exception..." + str(e))
        raise (e)
    if cmd in config.keys():
        if cmd in ['system']:
            return ("ERROR: Section readonly! "+cmd)
        else:
            return (set_param_handler(config[cmd],cmds))
    else:
        return ("Error: instrument or device not recognized not recognized! "+cmd)



def get_param_handler(section,params):
    
    try:
        param = params.pop(0).lower()
    except IndexError:
        return ("Error: No parameter given!")
    except Exception as e:
        print ("get_param_handler exception..." + str(e))
        raise(e)
    #print ("param:"+param)
    if param in section.keys():
        return (section[param])
    elif '' == param:
        return ("Error: parameter not recognized! "+cmd)
    elif ':' in param[0]:
        #return (json.dumps(list(section.keys())))
        return (json.dumps(section,indent=2,sort_keys=True))
    else:
        return ("Error: parameter not recognized! "+param)

def set_param_handler(section,params):
    #print (params)
    try:
        param = params.pop(0).lower()
    except IndexError:
        return ("Error: No  parameter given!")
    except Exception as e:
        print ("set_param_handler exception..." + str(e))
        raise(e)
    
    try:
        value = params.pop(0)
    except IndexError:
        return ("Error: No  value given!")
    except Exception as e:
        print ("set_param_handler exception..." + str(e))
        raise(e)
    value = convert_string_to_value(param,value)

    if param in section.keys():
        section[param] = value
        return (section[param])
    else:
        return ("Error: parameter not recognized! "+param)

def exit_handler(config):
    
    reply = "received shutdown command: TIP is going down\n"
    config['system']['abort'] = True
    sys.exit()
    return(reply)


if __name__  ==  "__main__":
    from lib.tip_config import config, load_config, convert_to_dict

    config = convert_to_dict(load_config())
    request = "GET/mxc/active"
    print (parse_request(request))

    request = "/get/mxc/:"
    print(parse_request(request))
 
    request = "s/mxc/active/1"
    print(parse_request(request))

    request = "s/mxc/control_default_heat/123.54"
    print(parse_request(request))

    request = "/g/mxc/:"
    print(parse_request(request))

    request = "version"
    print(parse_request(request))
    
    #request = "exit"
    #print(parse_request(config, request))

    #request = "config"
    #print(parse_request(config, request))

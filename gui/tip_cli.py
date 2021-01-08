#!/usr/bin/env python

import cmd
from lib.tip_zmq_client_lib import TIP_clients


class tipcli(cmd.Cmd):
    intro = 'Welcome to the tip shell. Type help or ? to list commands.\n'
    prompt = '(tip) '
    tc = TIP_clients()

    # ----- basic tip commands -----
    def do_g(self,arg):
        """
        get values from a tip service
        shortcut: 'g'
        options:
        get devices: 'get' or 'get :'
        get device parameters: 'get device' or 'get device :'
        get a device parameter: 'get device param'
        """
        return self.do_get(arg)

    def do_get(self, arg):
        """
        get values from a tip service
        shortcut: 'g'
        options:
        get devices: 'get' or 'get :'
        get device parameters: 'get device' or 'get device :'
        get a device parameter: 'get device param'
        """
        #print(arg)
        args = arg.split()
        if len(args) == 0:
            print(self.tc.get_devices())
        elif len(args) == 1:
            if args[0] == ':':
                print(self.tc.get_devices())
            else:
                print(self.tc.get_device(args[0]))
        elif len(args) == 2:
            print(self.tc.get_param(args[0],args[1]))
        else:
            print("Not recognized: "+arg)
        return
    def do_s(self,arg):
        """
        set values at a tip service
        shortcut: 's'
        options:
        set param: 'set device param'
        """
        return self.do_set(arg)

    def do_set(self, arg):
        """
        set values at a tip service
        shortcut: 's'
        options:
        set param: 'set device param'
        """
        args = arg.split()
        if len(args) < 3:
            print("set device param value")
        elif len(args) == 3:
            print(self.tc.set_param(args[0],args[1],args[2]))
        else:
            print("Not recognized: "+arg)
        return
    def do_exec(self, arg):
        'exec '
        pass

    # ----- record and playback -----
    """
    def precmd(self, line):
        print(line)
        return line.split()
    """
    def do_q(self,arg):
        "quit tip cli"
        exit()
    """
    def close(self):
        if self.file:
            self.file.close()
            self.file = None
    """


if __name__ == '__main__':
    tipcli().cmdloop()
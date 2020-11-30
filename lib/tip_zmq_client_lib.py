#
#  a set of convenient functions to talk to a TIP server.  
#   
#  
#

import zmq
import time
import timeit
import json

context = zmq.Context()
socket = context.socket(zmq.REQ)
#  Socket to talk to server
#socket = None

def setup_connection(url="tcp://localhost:5000"):
    print("Connecting to TIP server " +str(url))
    socket.setsockopt(zmq.RCVTIMEO,1000) # wait no longer than a second to fail.
    socket.setsockopt(zmq.LINGER,0)
    socket.connect(url)
    try:
        # make sure auth has worked ...
        # check IP configuration if it fails here
        socket.send_string("/ping")
        message = socket.recv_string()
        if message == "pong": 
            return True
        else: 
            return False
    except zmq.error.Again:
        print("ERROR: Server not available or auth failed!")
        return False

def close_connection():
    print("Closing connection to TIP server…")
    socket.close()

def set_param(device, param, value):
    socket.send_string("set/"+device+"/"+param+"/"+str(value))
    message = socket.recv_string()
    return (message)

def get_param(device, param):
    socket.send_string("get/"+device+"/"+param)
    message = socket.recv_string()
    return (message)

def get_device(device):
    socket.send_string("get/"+device+"/:")
    message = socket.recv_string()
    return json.loads(message)

def get_devices():
    socket.send_string("get/:")
    message = socket.recv_string()
    return json.loads(message)

def get_config():
    socket.send_string("get/::")
    message = socket.recv_string()
    return json.loads(message)

def set_exit():
    return socket.send_string("EXIT")


def test_speed():
    #  Do 10 requests, waiting each time for a response// debugging code
    for request in range(10):
        print("Sending request %s …" % request)
        socket.send_string("get/::")
        
        #  Get the reply.
        message = socket.recv_string()
        print (len(message))
        print("Received reply %s [ %s ]" % (request, json.loads(message)))


        #time.sleep(0.1)

class TIP_clients(object):
    "This class allows to talk to several tip server"
    def __init__(self,url="localhost:5000"):
        self.url = url
        from threading import Lock
        self.get_lock = Lock()

        self.context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.setup_connection(url="tcp://"+url)

    def setup_connection(self,url="tcp://localhost:5000"):
        print("Connecting to TIP server " +str(url))
        self.socket.setsockopt(zmq.RCVTIMEO,1000) # wait no longer than a second to fail.
        self.socket.setsockopt(zmq.LINGER,0)
        self.socket.connect(url)
        try:
            # make sure auth has worked ...
            # check IP configuration if it fails here
            self.socket.send_string("/ping")
            message = self.socket.recv_string()
            if message == "pong": 
                return True
            else: 
                return False
        except zmq.error.Again:
            print("ERROR: Server not available or auth failed!")
            return False

    def close_connection(self):
        print("Closing connection to TIP server…")
        self.socket.close()

    def set_param(self,device, param, value):
        with self.get_lock:
            self.socket.send_string("set/"+device+"/"+param+"/"+str(value))
            message = self.socket.recv_string()
            return (message)

    def get_param(self,device, param):
        with self.get_lock:
            self.socket.send_string("get/"+device+"/"+param)
            message = self.socket.recv_string()
            return (message)

    def get_device(self,device):
        with self.get_lock:
            self.socket.send_string("get/"+device+"/:")
            message = self.socket.recv_string()
            return json.loads(message)

    def get_devices(self):
        with self.get_lock:
            self.socket.send_string("get/:")
            message = self.socket.recv_string()
            return json.loads(message)

    def get_config(self):
        with self.get_lock:
            self.socket.send_string("get/::")
            message = self.socket.recv_string()
            return json.loads(message)

    def set_exit(self):
        return self.socket.send_string("EXIT")


if __name__ == "__main__":
    import sys
    # if setup_connection(url=sys.argv[1]):
    #     #test_speed()
    #     #print(timeit.timeit("test_speed()",setup="from __main__ import test_speed",number = 100))
    #     print(get_devices())
    #     print(get_param("mxc","temperature"))
    TC = TIP_clients("localhost:5000")
    print(TC.get_devices())
    for i in range(100):
        time.sleep(0.3)
        print(TC.get_param("mxc","temperature"))

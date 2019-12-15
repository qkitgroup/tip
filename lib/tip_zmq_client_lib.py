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
    print("Connecting to TIP server…")
    socket.connect(url)

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


if __name__ == "__main__":

    #test_speed()
    #print(timeit.timeit("test_speed()",setup="from __main__ import test_speed",number = 100))
    print(get_devices())
    print(get_param("mxc","control_resistor"))
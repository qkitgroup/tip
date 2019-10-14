
import time
import threading
import logging
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator
#from zmq.auth import Authenticator
from lib.tip_config import config
from lib.tip_srv_lib import parse_request

def serve_requests ():
    context = zmq.Context()
    # FIXME: authentication is not working in the moment
    #auth = ThreadAuthenticator(context)
    #auth = Authenticator(context)
    #auth.start()
    #auth.allow('127.0.0.1')
    #auth.allow('localhost')
    #auth.allow('192.168.0.1')
    #auth.deny('localhost')

    socket = context.socket(zmq.REP)
    #socket.zap_domain = b'global'
    socket.bind("tcp://*:"+str(config['system'].get('zmq_port',5000)))

    while True:
        #  Wait for next request from client
        message = socket.recv_string()
        logging.debug("Received request: %s" % message)
        #  Send reply back to client:
        #  everything is handled by the tip_srv_lib parse_request
        socket.send_string(parse_request(message))
    
    #auth.stop()

def srv_thread():
    thread = threading.Thread( target = serve_requests, args = () )
    thread.start()
    time.sleep(10)
    


if __name__ == "__main__":
    from lib.tip_config import config, load_config, convert_to_dict
    config = convert_to_dict(load_config())
    #serve_requests()
    srv_thread()
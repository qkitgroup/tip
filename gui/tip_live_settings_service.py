#!/usr/bin/env python
# Simple webservice to modify the TIP live settings.
# -- should be run only from a local machine for now ---
#
# In the TIP directory run it by:
# python -m gui.tip_live_settings_service
# and open a http browser page e.g. at 
# http://localhost:8080
#
# Limitations:
# - TIP has to run for this service to be able to work
# - If a device was switched off (by a TIP setting active = False) 
#   it cannot be activated again in the live settings. For this 
#   TIP has to be restarted. Also the "active devices" entry is not 
#   updated.
# - no security checking
# - no settings file
#
# Changelog
# written for TIP 2 by HR@KIT 2022 

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse

import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(
                  os.path.dirname(__file__), 
                  os.pardir)
)
sys.path.append(PROJECT_ROOT)

from lib.tip_zmq_client_lib import TIP_clients

HTTP_hostName = "localhost"
HTTP_serverPort = 8080

TIP_server = "localhost"
TIP_port   = 6000



class TIP_LSS(BaseHTTPRequestHandler):
    "TIP Live Settings Service"
    def do_GET(self):
        self.tip = TIP_clients(url=TIP_server+":"+str(TIP_port))
        tip_devices = self.tip.get_devices()
        tip_config = self.tip.get_config()

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        parsed_path = parse.urlparse(self.path)
        #print (parsed_path.query)
        if parsed_path.query:
            self.get_tip_cmd(parsed_path.query)
            dev,param,nval = self.get_tip_cmd(parsed_path.query)
            self.tip.set_param(dev,param,nval)
            self.wfile.write(bytes(self.html_header(1)))
        else:
            self.wfile.write(bytes(self.html_header(180)))
        self.wfile.write(bytes(self.html_body_start(tip_devices,tip_config)))
        self.wfile.write(bytes(self.html_table_start()))
        for tdevice in tip_devices :
            self.wfile.write(bytes(self.html_device_block_start(tdevice)))
            for param in tip_config[tdevice]:
                value = tip_config[tdevice][param]
                self.wfile.write(bytes(self.html_table_row(tdevice,param,value)))
            self.wfile.write(bytes(self.html_device_block_end()))
        self.wfile.write(bytes(self.html_table_end()))
        
        self.wfile.write(bytes(self.html_body_end()))


    def get_tip_cmd(self,get_string):
        "retrieve the cmd from the http get string"
        cmd_arr = [i.split('=') for i in get_string.split('&')]
        dev = ''
        param =''
        nval = '' 
        for c in cmd_arr:
            if c[0] == 'device':
                dev = c[1]
            if c[0] == 'param':
                param = c[1]
            if c[0] == 'nval':
                nval = c[1]

        #cmd = f"s/{dev}/{param}/{nval}"
        #print(cmd)

        return dev,param,nval

    def html_header(self,refresh_time=60):
        header = """<!DOCTYPE html>
        <html>
        <head>
        """
        header += f'<meta http-equiv="refresh" content="{refresh_time}; url=http://localhost:8080">'
        header += """
        <style>
        body {background-color: #E4E6F0;}
        .button {
            border: none;
            color: white;
            padding: 5px 5px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 12px;
            margin: 1px 1px;
            cursor: pointer;
        }

        .button1 {background-color: #4CAF50;} /* Green */
        .button2 {background-color: #008CBA;} /* Blue */
        .button3 {background-color: #3551DE;} /* dark blue */


        .top_line   {display:block;}
        .float_right {float:right; }
        .float_left  {float:left; }
        .top_bmk    {display:block;}
        .deviceblock {border:1px solid black; border-radius: 6px; padding: 5px 5px; margin:10px;}
        .table    {display:block;}
        .row      {display:inline-block; width: 49%;}
        .cell_dev {display:inline-block; width: 100px; color: blue}
        .cell_par {display:inline-block; width: 180px; color: green}
        .cell_val {display:inline-block; width: 200px; color: red}
        .cell_inp {display:inline-block; width: 200px;}

        </style>
        </head>"""
        return header.encode("UTF-8")
    
    
    def html_body_start(self,devices,config):
        body_str =  f"""
        <body>
        <div><!--
            <div class="float_right">
            <form action="/" method="get">
                <button type="submit"  class="button button1">save</button>
            </form>
            </div> -->
            <div class="float_right">
            <form action="/" method="get">
                <button type="submit" class="button button2">refresh</button>
            </form>
            </div>
        </div>
        <h3> TIP live config </h3>
        <h4>Devices defined in TIP:</h4>
        """
        for device in devices:
            body_str += f"""<div align="center" class="float_left"><a href="#{device}"><button class="button button3">{device}</button></a></div>\n"""
        body_str += "<br><br><h4>Active devices</h4>"
        for device in config['system']['active_devices']:
            body_str += f"""<div align="center" class="float_left"><a href="#{device}"><button class="button button3">{device}</button></a></div>\n"""
        body_str += "<br><h4>Active instruments</h4>"
        for device in config['system']['active_instruments']:
            body_str += f"""<div align="center" class="float_left"><a href="#{device}"><button class="button button3">{device}</button></a></div>\n"""


        body_str += '</div><br><br><br>\n'
        
        return body_str.encode("UTF-8")


    def html_body_end(self):
        return """\n</body>
                    </html>""".encode("UTF-8")

    def html_device_block_start(self,device):
        return f"""\n<div class="deviceblock" id="{device}" >
                <h4>{device}</h4>""".encode("UTF-8")
    def html_table_start(self):
        return """\n<div class="table">""".encode("UTF-8")

    def html_table_row(self,device,param,value):

        row = f"""
        <div class="row">
          <div class="cell_par">
             {param}
          </div>
          <div class="cell_val">
             {value}
          </div>
          <div class="cell_inp">
            <form action="/" method="get">
               <input type="text" id="nval" name="nval" value"">
               <input type="hidden" name="device" id="{device}" value={device} />
               <input type="hidden" name="param"  id="{param}"  value={param}  />
               <button type="submit" class="button button1" ">update</button>
            </form>
          </div>
        </div>
        """
        return row.encode("UTF-8")
    def html_table_end(self):
        return "</div>".encode("UTF8")
        
    def html_device_block_end(self):
        return "</div>".encode("UTF-8")
        


if __name__ == "__main__":        
    webServer = HTTPServer((HTTP_hostName, HTTP_serverPort), TIP_LSS)
    print("TIP live settings service (LSS) started http://%s:%s" % (HTTP_hostName, HTTP_serverPort))

    
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass    

    webServer.server_close()
    print("Server stopped.")


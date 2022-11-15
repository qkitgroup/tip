#
# This file mainly handles the data log recording (DLR) to external devices
# in the moment we only use the external data facility "influxdb"
# TIP 2.0 HR@KIT 2022
#
# logging structure:
# DLR gets periodically called and looks at the global DLR queue "DLR_queue", 
# where the name of the device is appended by the instrument/device
# -> then the data is loaded from the config
# -> and submitted to the influxdb
# -> the next entry of the queue is processed
# if a device has already been processed, it is IGNORED the next time.
# DLR entry : ( device , time )

import logging
from queue import Empty

from lib.tip_config import config, internal

dlr_queue  = internal['dlr_queue']

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, WritePrecision
from time import time
from random import random

class data_log_recorder(object):
    def __init__(self,name):
        self.name  = name 
        self.backend = 0 # no backend yet
        self.control_device = 0
        self.schedule_priority = 1
        self.scheduler = None
        #config[name]['change_time'] = 0
        # taken from config 
        self.influxdb_url     = "http://localhost:8086"
        self.influxdb_bucket  = "homebkt"
        self.influxdb_token   = "KzmG8NueJP7j..."
        self.influxdb_org     = "myorg"
        
        


    def schedule(self):
        """
        This function is called recursively with schedule_periode delays 
        from the scheduler. The scheduler is called after execute_func has been executed again, 
        which means that the total periode is schedule_periode+duration_of(execute_func).
        """
        logging.debug("exec schedule() for " + self.name)
        logging.debug(self.name +" "+str(config[self.name]['interval']))


        if not config[self.name]['active']: return

        # this function does the heavy lifting 
        self._execute_func()

        # if abort is changed while _execute_func() is running, it would need another cycle, thus: 
        if not config[self.name]['active']: return  

        # recursive hook into the scheduler queue:
        self.scheduler.enter(config[self.name]['interval'], 
            self.schedule_priority, 
            self.schedule)
    
    #class influxdb_backend(object):
    def _execute_func(self):
        self.process_dlr()

    def process_dlr(self):
        dlrq = internal['dlr_queue']
        devitems_val   = {}
        devitems_time  = {}
        devitems_dev   = {}
        devitems_item  = {}
        
        #for d in devs:
        while (not dlrq.empty()):
            dlr_dg = dlrq.get()
            #print(dlr_dg.device,dlr_dg.item,dlr_dg.value,dlr_dg.change_time)
            key = dlr_dg.device + dlr_dg.item
            
            # prepare to downsample (average) values 
            if key not in devitems_val:
                devitems_val[key]   = [dlr_dg.value]
                devitems_dev[key]   = dlr_dg.device
                devitems_item[key]  = dlr_dg.item
                devitems_time[key]  = dlr_dg.change_time
            else:
                devitems_val[key].append(dlr_dg.value)
                devitems_dev[key]   = dlr_dg.device
                devitems_item[key]  = dlr_dg.item
                devitems_time[key]  = dlr_dg.change_time


        for key in devitems_val:
            # calculate the value average 
            val_avg = sum(devitems_val[key])/len(devitems_val[key])
            #print ("DLR val_avg",val_avg)
            # define the influxdb data point
            ifp = self._influxdb_point(
                devitems_dev[key],
                devitems_item[key],
                val_avg,
                devitems_time[key]
            )
            # submit it to the influxdb
            self._submit_to_influxdb(ifp)



    def _influxdb_point (self,device,item,value,change_time):
        """
            format in influxdb ?
            _table	_measurement _field _value          _start _stop _time
            0	temperature	mxc	0.01485230271700029	    2022-11-14T21:07:58.853Z	2022-11-14T22:07:58.853Z	2022-11-14T21:08:10.000Z
        """

        return Point.measurement(item)\
            .field(device,value)\
            .time(int(change_time*1e9))


            
 
    def _submit_to_influxdb(self,influxdb_point):
        
        logging.debug ("DLR submit to influxdb:", str(influxdb_point.to_line_protocol()))

        client = InfluxDBClient(
            url    = config[self.name]['influxdb_url'], 
            token  = config[self.name]['influxdb_token'],
            org    = config[self.name]['influxdb_org']
         )
        
        write_api = client.write_api(write_options=SYNCHRONOUS)

        write_api.write(
            bucket = config[self.name]['influxdb_bucket'], 
            record = influxdb_point
            )
           
    
    def _append_to_devitem_queue(self):
        pass

    def prepare_influx_datagram(self, dlr_dg):
        pass

    def send_to_influxdb(self):
    
        url = self.influxdb_url
        bucket = self.influxdb_bucket
        token = self.influxdb_token
        org = self.influxdb_org

        client = InfluxDBClient(url=url, token=token, org=org)

        write_api = client.write_api(write_options=SYNCHRONOUS)
        #write_api = client.write_api()
    
        p = Point.measurement("vacuum")\
            .tag("chamber", "cosi-main")\
            .field("pressure", 10e-6*random())\
            .time(int(time()*1e9))        #,write_precision=WritePrecision.NS)
        print (p.to_line_protocol())
        write_api.write(bucket=bucket, record=p)

    def _convert_to_influxdb_timestamp(self,change_time):
        # an integer representing epoch nanoseconds
        return int(change_time*1e9)

    def _get_dlr_item(self):
        try:
            device = dlr_queue.get(block=False)
        except Empty:
            return None 



if __name__ ==  "__main__":
    dlr =  data_log_recorder("test")
    dlr.send_to_influxdb()
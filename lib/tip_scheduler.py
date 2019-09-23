#!/usr/bin/env python
# Scheduler for tip
# written for TIP 2.0 by HR@KIT 2019

import sched,time
import threading

from .tip_devices import device,thermometer
       


class tip_scheduler(object):
    def __init__(self):
        # we operate a scheduler for every device backend
        # where e.g. a resistance bridge is a backend
        self.schedulers={}
        self.scheduler_threads = []
        self.devices = {}



    def add_device(self,device):
        " function to add a device to be scheduled "
        # firt reset abort variable
        device.abort = False
        # is there already a scheduler on a specific backend?
        self.devices[device.name] = device
        scheduler = self.schedulers.get(device.backend,False)
        
        if not scheduler:
            # create a new scheduler and save it for later use
            scheduler = sched.scheduler(time.time, time.sleep)
            self.schedulers[device.backend] = scheduler
        
        device.scheduler = scheduler

        scheduler.enter(device.schedule_periode,
            device.schedule_priority, 
            device.schedule)
   
   
    def add_thermometer(self,thermometer):
        "proxy func"
        return self.add_device(thermometer)

    def run(self):
        # executes the scheduler
        # the schedulers are blocking, so everyone has to run in a separate thread
        # 
        # scheduler.run() starts the scheduler
        for scheduler in self.schedulers.values():
            th= threading.Thread(target=scheduler.run, args=())
            self.scheduler_threads.append(th)
            th.start()
            
        
    def stop(self, device = ""):
        # by default (device= None) all scheduler events are stopped
        # if "device" is given (e.g. a thermometer object), 
        # only this device is removed from the scheduler queue
        if self.devices.get(device,False):
            print("Scheduler: removing "+device)
            self.devices[device].abort = True            

        else:
            print ("Scheduler: removing all tasks from the event queue.")
            for dev in self.devices.values(): 
                dev.abort = True
            self.devices = {}
            for scheduler in self.schedulers.values():
                for event in scheduler.queue:
                    scheduler.cancel(event)
            print(scheduler.queue)
        
            


if __name__ == "__main__":
    tip_sched  = tip_scheduler()
    tm = 1

    ts = {}
    backends  = ["SIM921","LR700","AVS47"]

    for t in ["mxc","1kt","He4"]:
        print(t)
        ts[t] = thermometer(t)
        ts[t].backend = backends.pop()

        ts[t].schedule_periode = tm
        tm+=2
        tip_sched.add_thermometer(ts[t])
    
    tip_sched.run()

    time.sleep(6)
    tip_sched.stop("mxc")
    time.sleep(10)
    tip_sched.stop()
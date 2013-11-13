#!/usr/bin/env python
import h5py
from time import time
class H5_LOGFILE(object):
    def __init__(self,filename):
        self.open_file(filename)
        
    def open_file(self,filename):
        try: 
            f = h5py.File(filename, "w")
        except e:
            print "error in opening file: ",e
            
        if 'log' in f: 
            self.log = f['log']
        else:
            self.log = f.create_group('log')
        
        self.logfile = f    
        #return self.log
        
    def close_file(self):
        self.logfile.close()
    
    def append(self,sink, value):
        length = len(sink[0])
        sink[0].resize((length+1,))
        sink[1].resize((length+1,))
        sink[0][-1] = value
        sink[1][-1] = time()
        
    def new_sink(self,log_item, log_item_type = 'i', log_interval = 1):
        "sink is a storage space for items at a given time to log"
        dset      = self.log.create_dataset(log_item, 
                                            (1,),
                                            maxshape=(None,),
                                            #compression = 'gzip',
                                            dtype=log_item_type)
        dset_time = self.log.create_dataset(log_item+"_time",
                                            (1,),
                                            maxshape=(None,),
                                            #compression = 'gzip',
                                            dtype='=f8')        
        return (dset, dset_time) 
        #setattr(self,log_item,dset)
        
if __name__ == "__main__":
    
    log = H5_LOGFILE("test.h5")
    T_4K = log.new_sink('T_4K')
    log.new_sink('T_MC')
    log.new_sink('T_1K')
    for i in xrange(200):
        log.append(T_4K,1223*i)
    
    print T_4K[1][23]
    log.close_file()
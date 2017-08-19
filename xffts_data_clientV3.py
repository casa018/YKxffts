
import struct
import socket
import numpy
import time
import os

class xffts_data_client(object):
    _sock = None
    _fp = None
    
    def __init__(self, host=None, port=None):
        if (host is not None)&(port is not None):
            self.set_socket(host, port)
            pass
        pass

    def set_socket(self, host, port):
        sock = socket.socket()
        sock.connect((host, port))
        self._sock = sock
        self._fp = sock.makefile()
        return self._fp
    
    def getspectrum(self, integ_sec, repeat=1, start_time=0, ram_mode=True, storage_mode=False, dirname=None):
        if storage_mode:
            if (dirname is None):
                current_time = time.strftime('%Y%m%d_%H%M%S')
                dirname = '%s_getspectrum(_%.1f,_%d,_%.2f)' %(current_time, integ_sec, repeat, start_time)
                pass
            os.mkdir(dirname)
            os.chdir(dirname)
            pass
        
        command = '%f %d %f\n'%(integ_sec, repeat, start_time)
        self._fp.write(command)
        self._fp.flush()
        
        received_data = []
        timestamp_data = []
        
        while True:
            reply = self._fp.readline()
            
            if reply=='\n': continue
            elif reply=='FIN-ALL\n': break
            elif reply.split()[0]=='RECEIVED:': continue
            elif reply.split()[0]=='FIN:': continue
            elif reply.split()[0]=='INFO:':
                be_total_num = int(reply.split()[1].split('=')[-1])
                if received_data==[]:
                    received_data = [[] for i in range(be_total_num)]
                    pass
            elif reply.split()[0]=='SendingSyncData':
                be_num_str, dsize_str, repeat_str = reply.split()[1:]
                be_num = int(be_num_str.split('=')[-1])
                dsize = int(dsize_str.split('=')[-1])
                repeat = int(repeat_str.split('=')[-1])
                spectrum = self._fp.read(dsize)
                spectrum = struct.unpack('%df'%(dsize/4), spectrum)
                if ram_mode:
                    received_data[be_num].append(spectrum)
                    pass
                if storage_mode:
                    numpy.save('loop%d_spectrum%d'%(repeat, be_num),spectrum)
                    pass
                pass
            elif reply.split()[0]=='SendingTimeStamps':
                tsnum_str, repeat_str = reply.split()[1:]
                tsnum = int(tsnum_str.split('=')[-1])
                repeat = int(repeat_str.split('=')[-1])
                dsize = tsnum*8
                timestamp = self._fp.read(dsize)
                timestamp = struct.unpack('%dd'%tsnum, timestamp)
                if ram_mode:
                    timestamp_data.append(timestamp)
                    pass
                if storage_mode:
                    numpy.save('loop%d_timestamp'%repeat, timestamp)
                    pass
                pass
            continue
        
        if storage_mode: os.chdir('..')
        return [numpy.array(received_data), timestamp_data]
    
    def delay_calibration(self):
        synctime = 0.1
        start_time = time.time() + 5*numpy.random.uniform()
        spectrum, timestamp = self.getspectrum(synctime, 1, start_time)
        delay = start_time - timestamp[0][0]
        if abs(delay) > synctime/2.0:
            shift_sync = delay/synctime
            shift_syncnum = int(shift_sync)
            if abs(shift_sync-int(shift_sync)) >= 0.5: shift_syncnum += int(shift_syncnum/abs(shift_syncnum))
            command = 'DelayCalibration %d\n'%(shift_syncnum)
            self._fp.write(command)
            self._fp.flush()
        return shift_syncnum

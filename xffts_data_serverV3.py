
import time
import datetime
import socket
import struct
import threading
import numpy

class ring_buffer(object):
    buff_size = 1024
    data = None
    cur = 0
    cindex = 0
    _event = threading.Event()
    _reqnum = None
    
    def __init__(self, size=None):
        if size is not None: self.buff_size = int(size)
        self.data = [None] * self.buff_size
        pass
    
    def append(self, x):
        self.data[self.cindex] = x
        self.cur += 1
        self.cindex = self.cur % self.buff_size
        if self._reqnum == self.cur:
            self._event.set()
            self._event.clear()
            self._reqnum = None
            pass
        return
    
    def tolist(self, n=0, reqnum=0):
        if not(0 < n <= self.buff_size): n = self.buff_size
        
        if reqnum > self.cur:
            self._reqnum = reqnum + 1
            self._event.wait()
            pass
        
        if self.cindex >= n:
            return self.data[self.cindex-n:self.cindex]
        
        return self.data[self.cindex-n:] + self.data[:self.cindex]


class xffts_header(object):
    header_size = 64
    
    def __init__(self, header):
        self.ieee = struct.unpack('<4s',header[0:4])[0]
        self.data_format = struct.unpack('4s', header[4:8])[0]
        self.package_length = struct.unpack('I', header[8:12])[0]
        self.BE_name = struct.unpack('8s' ,header[12:20])[0]
        self.timestamp = struct.unpack('28s', header[20:48])[0]
        self.integration_time = struct.unpack('I', header[48:52])[0]
        self.phase_number = struct.unpack('I', header[52:56])[0]
        self.num_BE_sections = struct.unpack('I', header[56:60])[0]
        self.blocking = struct.unpack('I', header[60:64])[0]
        self.data_size = self.package_length - self.header_size
        pass


class xffts_data_receiver(object):
    header_size = 64
    _sock = None
    _buff = None
    _name = 'xffts_data_receiver'
    _stop_loop = False
    _time = []
    
    def __init__(self, host=None, port=None, sock=None, buff=None):
        if (host is not None)&(port is not None):
            self.create_socket(host, port)
            sock = None
            pass
        if sock is not None: self.set_socket(sock)
        if buff is not None: self.set_buffer(buff)
        pass
    
    def set_socket(self, sock):
        print('%s: set new socket.'%(self._name))
        self._sock = sock
        return self._sock
    
    def create_socket(self, host, port):
        print('%s: create new socket. host=%s, port=%d'%(self._name, host, port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        return self.set_socket(sock)
    
    def set_buffer(self, buff):
        print('%s: set new buffer.'%(self._name))
        self._buff = buff
        return self._buff
    
    def receiving_loop(self):
        print('%s: start receiving loop.'%(self._name))
        while True:
            if self._stop_loop: break
            header = self.recv_header()
            #t0 = time.time()
            data = self.recv_data(header.data_size)
            self._buff.append([header.timestamp, header.num_BE_sections, data])
            #self._time.append(time.time() - t0)
            continue
        return
    
    def recv_header(self):
        header = self._sock.recv(self.header_size)
        return xffts_header(header)
    
    def recv_data(self, data_size):
        data = self._sock.recv(data_size, socket.MSG_WAITALL)
        return data
    
    def stop_loop(self):
        self._stop_loop = True
        return self._stop_loop


class xffts_data_sender(object):
    _name = 'xffts_data_sender'
    _switch = True
    _integ_loop = 8
    _delaynum = 0

    def __init__(self, port=None, buff=None):
        if port is not None: self.create_server_socket(port)
        if buff is not None: self.set_buffer(buff)
        pass
    
    def create_server_socket(self, port):
        import socket
        print('%s: create new server_socket. port=%d'%(self._name, port))
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #self._sock.bind(('192.168.100.33', port))
        self._sock.bind(('localhost', port))
        self._sock.listen(5)
        return self._sock

    def set_buffer(self, buff):
        print('%s: set new buffer.'%(self._name))
        self._buff = buff
        self._integ_loop = self._buff.buff_size
        return self._buff

    def runserver(self):
        self._switch = True
        while self._switch:
            print('accept waiting')
            conn, addr = self._sock.accept()
            print("CONNECTION FROM:", addr)
            """
            integlation_time(sec), number_of_samples, start_time
            
            example
            MJD  :  '1.0, 100, 56416.5947964'
            GC   :  '1.0, 100, 2013-05-04T19:17:12.3'
            UNIX :  '1.0, 100, 137676990.4'
            
            """
            while self._switch:
                print('recv waiting')
                d = conn.recv(1024)
                print('recv>> %s'%d)
                d_split = d.split()
                if len(d)==0:
                    del(conn)
                    break
                if (len(d_split)==2) & (str(d_split[0])=='DelayCalibration'):
                    self._delaynum += int(d_split[1])
                    continue
                if len(d_split)!=3: continue
                integlation_time = float(d_split[0])
                number_of_samples = int(d_split[1])          
                start_time = d_split[2]
                start_time = self.anycalender_to_unixtime(start_time)
                print 'UnixTime:',start_time
                #synctime = self.get_synctime()
                synctime = 0.1      #ATTENTON!
                integ_num = int(integlation_time/synctime)
                
                conn.send('RECEIVED: %s\n'%(d))
                conn.send('INFO: BEnumbers=%d\n'%(self.get_be_num()))
                
                (current_pctime, current_buffcur) = (time.time(), self._buff.cur)
                print(current_buffcur)
                waiting = start_time - current_pctime + synctime*self._delaynum
                if (waiting <= 0): (start_time, waiting) = (current_pctime, 0.0)
                print('START_TIME:%.2f / YOURPC_TIME:%.2f'%(start_time, current_pctime))
                print('waiting for %.2f [s] '%(waiting))
                waiting_syncnum = waiting/synctime
                buff_block_addr = current_buffcur + int(waiting_syncnum)
                if (waiting_syncnum - int(waiting_syncnum) >= 0.5): buff_block_addr += 1
                for i in range(number_of_samples):
                    i += 1
                    print('    repeat: %d/%d'%((i),number_of_samples))
                    target_addr = buff_block_addr+(i*integ_num)
                    print('        get data -- target: %d, integnum: %d'%(target_addr, integ_num))
                    integ_data, timestamp_data = self.super_integration(target_addr, integ_num)
                    print('        sending')
                    for j,backend_data in enumerate(integ_data):
                        print('            ......')
                        length = len(backend_data)
                        conn.send('SendingSyncData BEnum=%d size=%d repeat=%d\n'%(j, length*4, i))
                        send_bin = struct.pack('%df'%(length), *backend_data)
                        conn.send(send_bin)
                        continue
                    print('            ......')
                    nstamps = len(timestamp_data)
                    conn.send('SendingTimeStamps TSnum=%d repeat=%d\n'%(nstamps, i))
                    send_bin = struct.pack('%dd'%nstamps, *timestamp_data)
                    conn.send(send_bin)
                    conn.send('FIN: number_of_samples=%d\n'%(i))
                    print('    end--')
                    continue 
                conn.send('FIN-ALL\n')
                continue
            continue
        return

    def stop_loop(self):
        self._switch = False
        return

    def anycalender_to_unixtime(self, ttime):
        try:
            ttime = float(ttime)
	    if ttime >= 1e9:
                print('input_type:UnixTime')
                ret = self.unixtime_to_unixtime(ttime)
            elif 1e6 > ttime > 5e4:
                print('input_type:MJD')
                ret = self.mjd_to_unixtime(ttime)
            else:
                print('input_type:Now!')
                ret =  time.time()
            pass
        except:
            print('input_type:GC')
            ret = self.gc_to_unixtime(ttime)
            pass
        return ret
    
    def mjd_to_unixtime(self, mjd):
        return (mjd-40587)*24.*3600.

    def gc_to_unixtime(self, gc):
        t = datetime.datetime.strptime(gc,'%Y-%m-%dT%H:%M:%S.%f')
        return time.mktime(t.timetuple()) + t.microsecond / 1e6
    
    def timestamp_to_unixtime(self, timestamp):
        return self.gc_to_unixtime(timestamp[:24])
    
    def unixtime_to_unixtime(self, ttime):
        return ttime
    
    def get_be_num(self):
        return self._buff.tolist(1)[0][1]
    
    def get_synctime(self, n=100):
        timestamp_list = [temp[0] for temp in self._buff.tolist(n)]
        unixtimestamp = [self.timestamp_to_unixtime(ts) for ts in timestamp_list]
        unixtimestamp = numpy.array(unixtimestamp)
        synctime = numpy.average(unixtimestamp[1:]-unixtimestamp[:-1])
        print 'synctime:',synctime
        return synctime
    
    def super_integration(self, target_addr, integ_num):
        buff_flush_num = integ_num / self._integ_loop
        buff_remainder_num = integ_num - (buff_flush_num * self._integ_loop)
        spectrum_data = []
        timestamp_data = []
        
        for i in range(buff_flush_num):
            sub_target_addr = target_addr - buff_remainder_num - (buff_flush_num - i - 1)*self._integ_loop
            gathered_data = self._buff.tolist(self._integ_loop, sub_target_addr)
            spectrum, timestamp = self.integ_data(gathered_data)
            spectrum_data.append(spectrum)
            spectrum_data = [numpy.sum(spectrum_data, axis=0)]
            timestamp_data += timestamp
            continue
        
        gathered_data = self._buff.tolist(buff_remainder_num, target_addr)
        spectrum, timestamp = self.integ_data(gathered_data)
        spectrum_data.append(spectrum)
        integrated_spec = numpy.sum(spectrum_data, axis=0)/integ_num
        timestamp_data += timestamp
        return [integrated_spec, timestamp_data]
    
    def integ_data(self, data):
        backends_num = data[0][1]
        backends = [[] for i in range(backends_num)]
        timestamp_data = []
        
        for syncdata in data:
            timestamp = syncdata[0]
            timestamp = struct.unpack('28s', timestamp)
            timestamp_data.append(self.timestamp_to_unixtime(timestamp[0])+(9.*60.*60.))
            #backends_num = syncdata[1]
            rawdata = syncdata[2]
            counter = 0
            for j in range(backends_num):
                benum, chnum = struct.unpack('2I', rawdata[counter:counter+8])
                counter += 8
                spec = struct.unpack('%df'%chnum, rawdata[counter:counter+chnum*4])
                counter += chnum * 4
                backends[j].append(spec)
                continue
            continue
        
        integrated_spec = numpy.sum(backends, axis=1)
        return [integrated_spec, timestamp_data]
    
    
class xffts_data_server(object):
    _buff = None
    _client = None
    _data_sender = None
    
    def __init__(self, xffts_cntl_host, xffts_cntl_port, data_server_port):
        buff = ring_buffer()
        self._buff = buff
        
        self._client = xffts_data_receiver(host=xffts_cntl_host,
                                           port=xffts_cntl_port,
                                           buff=self._buff)
        
        self._data_sender = xffts_data_sender(port=data_server_port,
                                              buff=self._buff)
        pass
    
    def start(self):
        client_thread = threading.Thread(target=self._client.receiving_loop)
        client_thread.start()
        self._client_thread = client_thread
        
        server_thread = threading.Thread(target=self._data_sender.runserver)
        server_thread.start()
        self._server_thread = server_thread
        return
    
    def stop(self):
        self._client.stop_loop()
        self._data_sender.stop_loop()
        return



class xffts_udp_client(object):
    _host = ''
    _port = 0
    _sock = None
    _bufsize = 16*1024
    _print = True
    _used = [0]*32
    
    def __init__(self, host='localhost', port=16210):
        self.set_host(host)
        self.set_port(port)
        pass
    
    def set_host(self, host):
        self._host = host
        return self._host
    
    def set_port(self, port):
        self._port = port
        return self._port
    
    def print_on(self):
        self._print = True
        return self._print
    
    def print_off(self):
        self._print = False
        return self._print
    
    def open(self):
        import socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return self._sock
    
    def close(self):
        self._sock.close()
        self._sock = None
        return self._sock
    
    def send(self, msg):
        if self._print: print('SEND> %s'%(msg))
        msg += '\n'
        ret = self._sock.sendto(msg, (self._host, self._port))
        return ret

    def recv(self, byte):
        ret = self._sock.recv(byte)
        if self._print: print('RECV> %s'%(ret))
        return ret
    
    def version(self):
        self.send('RPG:XFFTS:VERSION')
        ret = self.recv(self._bufsize)
	result = ret.split()[0] + ' ' + ret.split()[1]
	return result    

    def start(self):
        self.send('RPG:XFFTS:START')
        return self.recv(self._bufsize)

    def stop(self):
        self.send('RPG:XFFTS:STOP')
        return self.recv(self._bufsize)

    def abort(self):
        self.send('RPG:XFFTS:ABORT')
        return self.recv(self._bufsize)

    def configure(self):
        self.send('RPG:XFFTS:CONFIGURE')
        return self.recv(self._bufsize)

    def initialize(self):
        self.send('RPG:XFFTS:INITSYNTHESIZER')
        return self.recv(self._bufsize)

    #TODO::
    def set_state_enabled(self):
        self.send('RPG:XFFTS:STATE ENABLED')
        return self.recv(self._bufsize)

    #TODO::
    def set_state_disabled(self):
        self.send('RPG:XFFTS:STATE DISABLED')
        return self.recv(self._bufsize)
    
    def check_blanktime(self):
        self.send('RPG:XFFTS:BLANKTIME')
        ret = self.recv(self._bufsize)
        return int(ret.split()[1])
    
    def set_blanktime(self, usec):
        if usec < 1000 :
            print('ERROR:MINIMUM BLANKTIME IS 1000 [us]')
            return self.check_blanktime()
        self.send('RPG:XFFTS:CMDBLANKTIME %d'%(usec))
        ret = self.recv(self._bufsize)
        blanktime = int(ret.split()[1])
        return blanktime
    
    def check_synctime(self):
        self.send('RPG:XFFTS:SYNCTIME')
        ret = self.recv(self._bufsize)
        return int(ret.split()[1])

    def set_synctime(self,usec):
        if usec < 100000:
            print('ERROR:MINIMUM SYNCTIME IS 100,000 [us]')
            return self.check_synctime()
        self.send('RPG:XFFTS:CMDSYNCTIME %d'%(usec))
        ret = self.recv(self._bufsize)
        blanktime = int(ret.split()[1])
        return blanktime

    def check_numphases(self):
        self.send('RPG:XFFTS:NUMPHASES')
        ret = self.recv(self._bufsize)
        result = int(ret.split()[1])
        return result

    def set_numphases(self,phase):
	"""
	phase = [1,4]
	"""
        self.send('RPG:XFFTS:CMDNUMPHASES %d'%(phase))
        ret = self.recv(self._bufsize)
	result = int(ret.split()[1])
        return result

    def check_mode(self):
        self.send('RPG:XFFTS:MODE')
        ret = self.recv(self._bufsize)
	result = ret.split()[1]
	return result

    def set_mode(self, mode):
        """
        mode = INTERNAL | EXTERNAL
        """
        self.send('RPG:XFFTS:CMDMODE %s'%(mode))
        return self.recv(self._bufsize)

    def check_usedsections(self):
        self.send('RPG:XFFTS:USEDSECTIONS')
        ret = self.recv(self._bufsize)
        ret = ret.split()[1:-1]
        ret_int = map(int, ret)
        return ret_int

    def set_usedsections(self, section):
        """
        section :: list
        """
        #TODO:
        if len(section)!=32:
            section += [0] * (32-len(section))
            pass
        self._used = section
        section_str = ' '.join(map(str, section))
        self.send('RPG:XFFTS:CMDUSEDSECTIONS %s'%section_str)
        return self.recv(self._bufsize)

    def release_date(self):
        self.send('RPG:XFFTS:RELEASE')
        ret = self.recv(self._bufsize)
        return ret.split()[1]

    def caladc(self):
        self.send('RPG:XFFTS:CALADC')
        return self.recv(self._bufsize)

    def info(self, n):
        """
        boardnum::
        """
	self.send('RPG:XFFTS:INFO %d'%n)
	ret = self.recv(self._bufsize) 
        return int(ret.split()[1])

    def dump(self, n):
        """
        boardnum::
        """
	self.send('RPG:XFFTS:DUMP %d'%n)
	return self.recv(self._bufsize)

    def saveadcdelays(self):
        #self.send('RPG:XFFTS:SAVEADCDELAYS')
        #return self.recv(self._bufsize)
        pass

    def loadadcdelays(self):
        #self.send('RPG:XFFTS:LOADADCDELAYS')
        #return self.recv(self._bufsize)
        pass

    def check_board_numspecchan(self, n):
        self.send('RPG:XFFTS:BAND%d:NUMSPECCHAN'%n)
        ret = self.recv(self._bufsize)
        numspecchan = int(ret.split()[1])
        return numspecchan

    def set_board_numspecchan(self, n, chan):
        self.send('RPG:XFFTS:BAND%d:CMDNUMSPECCHAN %d'%(n,chan))
        ret = self.recv(self._bufsize)
        numspecchan = int(ret.split()[1])
        return numspecchan

    def check_board_bandwidth(self, n):
        self.send('RPG:XFFTS:BAND%d:BANDWIDTH'%n)
        ret = self.recv(self._bufsize)
        return float(ret.split()[1])

    def set_board_bandwidth(self, n, width):
        self.send('RPG:XFFTS:BAND%d:CMDBANDWIDTH %.2f'%(n,width))
        ret = self.recv(self._bufsize)
        bandwidth = ret.split()[1]
        if bandwidth == 'ERROR': return 'ERROR:INVALID_BAND MONEY!!'
        else : return float(bandwidth)

    def check_board_mirrorspectra(self, n):
        self.send('RPG:XFFTS:BAND%d:MIRROSPECTRA'%n)
        ret = self.recv(self._bufsize)
        if ret.split()[1] == '0':
            result = 'MIRROR OFF'
            pass
        elif ret.split()[1] == '1':
            result = 'MIRROR ON'
            pass
        else:
            result = 'ERROR:INVALID_BAND'
            pass
        return result

    def set_board_mirrorspectra(self, n, switch):
        self.send('RPG:XFFTS:BAND%d:CMDMIRROSPECTRA %d'%(n,switch))
        return self.recv(self._bufsize)

    def board_caladc(self,n):
        self.send('RPG:XFFTS:BAND%d:CALADC'%n)
        return self.recv(self._bufsize)

    def board_adcdelay(self,n):
        self.send('RPG:XFFTS:BAND%d:ADCDELAY'%n)
        ret = self.recv(self._bufsize)
        delay = float(ret.split()[1])
        return delay

    def board_time(self,n):
        self.send('RPG:XFFTS:BAND%d:TIME'%n)
        ret = self.recv(self._bufsize)
        time = ret.split()[1]
        return time

    def check_board_temperature(self, n):
        self.send('RPG:XFFTS:BAND%d:TEMPERATURE'%n)
        ret = self.recv(self._bufsize)
        temp =map(float,[ret.split()[1],ret.split()[2],ret.split()[3]])
        return temp
    
    def check_all_temperature(self):
        all_temp = []
        for i, used in enumerate(self.check_usedsections()):
            if used==1:
                ret = self.check_board_temperature(i+1)
                all_temp.append(ret)
            else:
                all_temp.append(None)
                pass
            continue
        return all_temp

    def board_specfilter(self, n):
        self.send('RPG:XFFTS:BAND%d:SPECFILTER'%n)
	ret = self.recv(self._bufsize)
        return int(ret.split()[1])



class xffts_data_client(object):
    _sock = None
    _fp = None
    
    def __init__(self, host=None, port=None):
        if (host is not None)&(port is not None):
            self.set_socket(host, port)
            pass
        pass

    def set_socket(self, host, port):
        import socket
        sock = socket.socket()
        sock.connect((host, port))
        self._sock = sock
        self._fp = sock.makefile()
        return self._fp
    
    def getspectrum(self, integ_sec, repeat=1, start_time=0):
        import struct
        import numpy
        command = '%f %d %f\n'%(integ_sec, repeat, start_time)
        self._fp.write(command)
        self._fp.flush()
        
        received_data = []
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
                be_num_str, dsize_str = reply.split()[1:]
                be_num = int(be_num_str.split('=')[-1])
                dsize = int(dsize_str.split('=')[-1])
                spectrum = self._fp.read(dsize)
                spectrum = struct.unpack('%df'%(dsize/4), spectrum)
                received_data[be_num].append(spectrum)
                pass
            continue
        
        return numpy.array(received_data)


class xffts(object):
    ctrl_client = None
    data_client = None
    
    def __init__(self, ctrl_host=None, ctrl_port=None,
                 data_host=None, data_port=None):
        if (ctrl_host is not None)&(ctrl_port is not None):
            self.create_ctrl_client(ctrl_host, ctrl_port)
            pass
        
        if (data_host is not None)&(data_port is not None):
            self.create_data_client(data_host, data_port)
            pass
        pass
    
    def create_ctrl_client(self, host, port):
        ctrl = xffts_udp_client(host, port)
        ctrl.open()
        self.ctrl_client = ctrl
        
        self.print_on = ctrl.print_on
        self.print_off = ctrl.print_off
        self.open = ctrl.open
        self.close = ctrl.close
        self.send = ctrl.send
        self.recv = ctrl.recv
        self.version = ctrl.version
        self.start = ctrl.start
        self.stop = ctrl.stop
        self.abort = ctrl.abort
        self.configure = ctrl.configure
        self.intialize = ctrl.initialize
        self.set_state_enabled = ctrl.set_state_enabled
        self.set_state_disavled = ctrl.set_state_disabled
        self.check_blanktime = ctrl.check_blanktime
        self.set_blanktime = ctrl.set_blanktime
        self.check_synctime = ctrl.check_synctime
        self.set_synctime = ctrl.set_synctime
        self.check_numphases = ctrl.check_numphases
        self.set_numphases = ctrl.set_numphases
        self.set_mode = ctrl.set_mode
        self.check_usedsections = ctrl.check_usedsections
        self.set_usedsections = ctrl.set_usedsections
        self.release_date = ctrl.release_date
        self.caladc = ctrl.caladc
        self.info = ctrl.info
        self.dump = ctrl.dump
        self.saveadcdelays = ctrl.saveadcdelays
        self.loadadcdelays = ctrl.loadadcdelays
        self.check_board_numspecchan = ctrl.check_board_numspecchan
        self.set_board_numspecchan = ctrl.set_board_numspecchan
        self.check_board_bandwidth = ctrl.check_board_bandwidth
        self.set_board_bandwidth = ctrl.set_board_bandwidth
        self.check_board_mirrorspectra = ctrl.check_board_mirrorspectra
        self.set_board_mirrorspectra = ctrl.set_board_mirrorspectra
        self.board_caladc = ctrl.board_caladc
        self.board_time = ctrl.board_time
        self.check_board_temperature = ctrl.check_board_temperature
        self.check_all_temperature = ctrl.check_all_temperature
        self.board_specfilter = ctrl.board_specfilter
        return
    
    def create_data_client(self, host, port):
        data = xffts_data_client(host, port)
        self.data_client = data
        
        self.getspectrum = data.getspectrum

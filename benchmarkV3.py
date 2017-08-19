import xffts_data_clientV3
import xffts_client
import numpy
import time
import os
import matplotlib.pyplot as plt

class xffts_benchmark(object):
    xffts_usedsection = None
    xffts_boardnum = None
    xffts_bandwidth = []
    xffts_numspecchan = []
    waiting_time = 1.0
    integ_sec = 1.0
    
    def __init__(self, xffts_data_client_host, xffts_data_client_port, signal_generator_host=None, signal_generator_port=None):
        self.xffts_data_client = xffts_data_clientV3.xffts_data_client(host=xffts_data_client_host, port=xffts_data_client_port)
        self.xffts_udp_client = xffts_client.xffts_udp_client()
        self.xffts_udp_client.open()
        self.xffts_udp_client.print_off()
        self.xffts_usedsection = self.xffts_udp_client.check_usedsections()
        self.xffts_boardnum = numpy.array(self.xffts_usedsection).sum()
        for i in range(self.xffts_boardnum):
            self.xffts_bandwidth.append(self.xffts_udp_client.check_board_bandwidth(i+1))
            self.xffts_numspecchan.append(self.xffts_udp_client.check_board_numspecchan(i+1))
        if (signal_generator_host is not None)&(signal_generator_port is not None):
            import pymeasure
            self.set_signal_generator(signal_generator_host=signal_generator_host, signal_generator_port=signal_generator_port)
    
    def set_signal_generator(self, signal_generator_host, signal_generator_port):
        self.signal_generator = pymeasure.signalgenerator('scpi', 'ethernet', signal_generator_host, signal_generator_port)
        self.signal_generator.set_power(-100,'dBm')
        self.signal_generator.output_on()
        return
    
    def auto_totalpower(self, w0, wmax=None, dw=None, wunit='dBm'):
        power_points = self.power_range(w0=w0, wmax=wmax, dw=dw, wunit=wunit)
        data = self.totalpower(frequency_points=frequency_points, power_points=power_points, funit=funit,wunit=wunit)
        return data
    
    def auto_channel_response(self, channel, f0, w0, fmax=None, wmax=None, df=None, dw=None, funit='MHz',wunit='dBm', dnchan=0):
    	frequency_points = self.frequency_range(f0=f0, fmax=fmax, df=df, funit=funit)
    	power_points = self.power_range(w0=w0, wmax=wmax, dw=dw, wunit=wunit)
    	data = self.channel_response(channel=channel, frequency_points=frequency_points, power_points=power_points, funit=funit, wunit=wunit, dnchan=dnchan)
    	return data
    
    def auto_channelcalib(self, channel, f0, w0, fmax=None, wmax=None, df=None, dw=None, funit='MHz',wunit='dBm'):
    	frequency_points = self.frequency_range(f0=f0, fmax=fmax, df=df, funit=funit)
    	power_points = self.power_range(w0=w0, wmax=wmax, dw=dw, wunit=wunit)
    	data = self.channelling(channel=channel, frequency_points=frequency_points, power_points=power_points, funit=funit,wunit=wunit)
    	return data
    
    def frequency_range(self, f0, fmax=None, df=None, funit='MHz'):
        if (fmax is not None)&(df is not None):
            fnum = int((fmax-f0)/df)
            frequency_points = numpy.array(range(fnum+1))*df+f0
        elif (fmax is not None): frequency_points = numpy.array([f0, fmax])
        else: frequency_points = numpy.array([f0])
        print "Frequency Points : [%s]" %funit
        print frequency_points
        return frequency_points
    
    def power_range(self, w0, wmax=None, dw=None, wunit='dBm'):
        if (wmax is not None)&(dw is not None):
            wnum = int((wmax-w0)/dw)
            power_points = numpy.array(range(wnum+1))*dw+w0
        elif (wmax is not None): power_points = numpy.array([w0, wmax])
        else: power_points = numpy.array([w0])
        print "Power Points : [%s]" %wunit
        print power_points
        return power_points
    
    def channelling(self, frequency_points, power_points, funit='MHz',wunit='dBm'):
    	peak_data = []
    	error_data = []
    	for i in range(len(power_points)):
            power = power_points[i]
            self.signal_generator.set_power(power, wunit)
            peak_series = []
            error_seruis = []
            for j in range(len(frequency_points)):
                frequency = frequency_points[j]
                self.signal_generator.set_freq(frequency, funit)
                time.sleep(self.waiting_time)
                spectrum = self.xffts_data_client.getspectrum(self.integ_sec, 1, 0)[0]
                peak_channel, mean_channel = peak_channel(spectrum)
                error = 2*abs(peak_channel-mean_channel)
                peak_series.append(peak_channel)
                error_series.append(error)
            peak_data.append(peak_series)
            error_data.append(error_series)
        return [peak_data, error_data]
    
    def totalpower(self, power_points, wunit='dBm', channels=None):
        _channels = False
        if (channels is not None):
            channels = numpy.array(channels)
            n = len(channels)
            _channels = True
        strat_time = time.strftime('%Y%m%d_%H%M%S')
        data = []
        try:
            for power in power_points:
                series = []
                self.signal_generator.set_power(power, wunit)
                print "set power, %d [%s]" %(power, wunit)
                time.sleep(self.waiting_time)
                spectrum = self.xffts_data_client.getspectrum(self.integ_sec, 1, 0)[0]
                total_power = (numpy.mean(spectrum, axis=2)).reshape(len(spectrum))
                series.append(total_power)
                if _channels:
                    for chan in channels:
                        channelpower = spectrum[:,0,chan]
                        channelpower = channelpower.reshape(lne(spectrum))
                        series.append(channelpower)
                print(series)
                data.append(series)
                i += 1
        except:
            print("SAVING_DATA")
            filename= "TotalPower_"+start_time+"_%d(%f-%f)[%s]" %(len(data), powerpoints[0], power, wunit)
            numpy.save(filename, data)
            self.totalpower_imaging(filename=filename, power_pints=power_points, wunit=wunit)
        return numpy.array(data)
    
    def linearity_manual(self):
        def linearity_imaging1(data, power, filename):
            x = power
            nominal_value = data.max()
            for i in range(self.xffts_boardnum):
                y = numpy.log10(data[:,i]/nominal_value)*10.0
                plt.plot(x,y,label="Slot%d"%(i+1))
            plt.xlabel("Input Power [dBm]")
            plt.ylabel("XFFTS Output [dB]")
            plt.title("XFFTS Linearity")
            plt.legend()
            plt.grid()
            plt.savefig("XFFTS_TotalPower_Linearity_Input:%.2f-%.2f[dBm].png" %(power.min,power.max))
            plt.close()
            return        
        start_time = time.strftime('%Y%m%d_%H%M%S')
        filename = "LinearityManual_%s" %start_time
        spectrum_data = []
        totalpower_data = []
        power_series = []
        try:
            loop = 1
            print("START!")
            while True:
                print("[ LoopNo: %d ]" %loop)
                loop += 1
                print("Input Power [dBm]")
                power = raw_input()
                power_series.append(power)
                print("  >>please wait ...")
                time.sleep(self.waiting_time)
                spectrum = self.xffts_data_client.getspectrum(self.integ_sec, 1, 0)[0]
                a,b,c = spectrum.shape
                spectrum = spectrum.reshape(a,c)
                totalpower = numpy.mean(spectrum, axis=2).reshape(self.xffts_boardnum)
                spectrum_data.append(spectrum)
                totalpower_data.append(totalpower)
        except:
            print("BREAK!")
            spectrum_data = numpy.array(spectrum_data)
            totalpower_data = numpy.array(totalpower_data)
            power_series = numpy.array(power_series)
        print("SAVING_DATA")
        numpy.save(filename+"_Spectrum", spectrum_data)
        numpy.save(filename+"_TotalPower", totalpower_data)
        numpy.save(filename+"_Power", power_series)
        print("Imaging...")
        #linearity_imaging1(data=totalpower_data, power=power_series, filename=filename)
        #linearity_imaging2(data=spectrum_data, power=power_series, filename=filename)
        return [spectrum_data, totalpower_data, power_series]
    
    def peak_point(self, frequency_points, power_points, funit='MHz',wunit='dBm'):
        def peak_point_imaging1(data, filename, frequency, power, funit, wunit):
            nominal_value = data[0,:,:].max()
            normalized_data = data[0,:,:]/nominal_value
            for i in range(self.xffts_boardnum):
                x = data[1,:,i]
                y = numpy.log10(normalized_data[:,i])*10.0
                plt.plot(x, y, label=("Slot=%d" %(i+1)))
            plt.xlabel("Channel [ch]")
            plt.ylabel("Output [dB]")
            plt.title("XFFTS Output: SGpower=%d[%s]" %(power, wunit))
            plt.legend()
            plt.grid()
            plt.savefig("XFFTS:SGpower=%d[%s]_SGfrquency(%.2f-%.2f)[%s].png" %(power, wunit, frequency_points.min(), frequency_points.max(), funit))
            plt.close()
            return
        def peak_point_imaging2(data, filename, frequency_points, power_points, funit, wunit):
            for i in range(self.xffts_boardnum):
                nominal_value = data[0,:,:,i].max()
                normalized_data = data[0,:,:,i]/nominal_value
                for j in range(len(power_points)):
                    x = data[1,j,:,i]
                    y = numpy.log10(data[0,j,:,i])*10.0
                    plt.plot(x, y, label=("SGpower=%d" %(power_points[j])))
                plt.xlabel("Channel [ch]")
                plt.ylabel("Output [dB]")
                plt.title("XFFTS Output Slot%d" %(i+1))
                plt.legend()
                plt.grid()
                plt.savefig("XFFTS:Slot%d_SGfrquency(%.2f-%.2f)[%s].png" %((i+1), frequency_points.min(), frequency_points.max(), funit))
                plt.close()
            return            
        obspoints = len(frequency_points)*len(power_points)
        print("Number of observing points: %d" %obspoints)
        start_time = time.strftime('%Y%m%d_%H%M%S')
        filename = "PeakPoint_"+start_time
        peakpower_data = []
        peakchannel_data = []
        loopnum = 1
        for power in power_points:
            self.signal_generator.set_power(power, wunit)
            print(">>SG Power: %f [%s]" %(power, wunit))
            peakpower_series = []
            peakchannel_series = []
            for frequency in frequency_points:
                print("[ %d / %d ]" %(loopnum, obspoints))
                loopnum += 1
                self.signal_generator.set_freq(frequency, funit)
                print(" -- SG Frequency setted: %f [%s]" %(frequency, funit))
                print("  ; waiting")
                time.sleep(self.waiting_time)
                print("  ; integrating data")
                spectrum = self.xffts_data_client.getspectrum(self.integ_sec, 1, 0)[0]
                print("  ; data received")
                peakpower = spectrum.max(axis=2)
                peakpower_series.append(peakpower.reshape(self.xffts_boardnum))
                peakchannel = numpy.where(spectrum == peakpower)[2]
                peakchannel_series.append(peakchannel)
            peak_point_imaging1(data=numpy.array([peakpower_series,peakchannel_series]), filename=filename, frequency=frequency_points, power=power, funit=funit, wunit=wunit)
            peakpower_data.append(peakpower_series)
            peakchannel_data.append(peakchannel_series)
        peakpower_data = numpy.array([peakpower_data])
        peakchannel_data = numpy.array([peakchannel_data])
        data = numpy.concatenate((peakpower_data, peakchannel_data), axis=0)
        numpy.save(filename, data)
        peak_point_imaging2(data=data, filename=filename, frequency_points=frequency_points, power_points=power_points, funit=funit, wunit=wunit)
        return data
    
    def channel_response(self, channel, frequency_points, power_points, funit='MHz',wunit='dBm', dnchan=0):
        def channel_imaging1(data, channel, frequency_points, power, funit, wunit):
            a,b,c,d = data.shape
            for i in range(a):
                nominal_value = data[i,0,:,:].max()
                normalized_data = data[i,0,:,:]/nominal_value
                for j in range(c):
                    filter_curve = numpy.log10(normalized_data[j,:])*10.0
                    plt.plot(frequency_points, filter_curve, label=("%dch" %(channel-(c-1)/2+j)))
                plt.xlabel("SG Frequency [%s]" %funit)
                plt.ylabel("Slot%d Output [dB]" %(i+1))
                plt.title("XFFTS:Slot%d_SGpower=%d[%s]" %((i+1), power, wunit))
                plt.legend()
                plt.grid()
                plt.savefig("XFFTS:Slot%d_SGpower=%d[%s]_SGfrquency(%.2f-%.2f)[%s].png" %((i+1), power, wunit, frequency_points[0], frequency_points[-1], funit))
                plt.close()
            return
        def channel_imaging2(data, channel, frequency_points, power_points, funit, wunit):
            a,b,c,d = data.shape
            for i in range(a):
                nominal_value = data[i,:,(c-1)/2,:].max()
                normalized_data = data[i,:,(c-1)/2,:]/nominal_value
                for j in range(b):
                    filter_curve = numpy.log10(normalized_data[j,:]/nominal_value)*10.0
                    plt.plot(frequency_points, filter_curve, label=("SGpower=%d [%s]" %(power_points[j],wunit)))
                plt.xlabel("SG Frequency [%s]" %funit)
                plt.ylabel("Slot%d %dch Output [dB]" %((i+1), channel))
                plt.title("XFFTS Slot%d %dch FilterCurve" %(i+1,channel))
                plt.legend()
                plt.grid()
                plt.savefig("XFFTS:Slot%d_%dch_SGpower_%d-%d[%s].png" %(i+1, channel, power_points[0], power_points[-1], wunit))
                plt.close()
            return
        obspoints = len(frequency_points)*len(power_points)
        print("Number of observing points: %d" %obspoints)
        start_time = time.strftime('%Y%m%d_%H%M%S')
        filename = "ChanRes_%.2f_%dch" %(start_time, channel)
        loopnum = 1
        for power in power_points:
            self.signal_generator.set_power(power, wunit)
            print(">>SG Power: %f [%s]" %(power, wunit))
            for frequency in frequency_points:
                print("[ %d / %d ]" %(loopnum, obspoints))
                loopnum += 1
                self.signal_generator.set_freq(frequency, funit)
                print(" -- SG Frequency setted: %f [%s]" %(frequency, funit))
                print("  ; waiting")
                time.sleep(self.waiting_time)
                print("  ; getting data")
                spectrum = self.xffts_data_client.getspectrum(self.integ_sec, 1, 0)[0]
                print("  ; data received")
                channel_power = spectrum[:,0,(channel-nchan):(channel+nchan+1)].reshape(self.xffts_boardnum,1,(1+2*nchan),1)
                if (frequency == frequency_points[0]): series = channel_power.copy()
                else: series = numpy.concatenate((series,channel_power),axis=3).copy()
            channel_imaging1(data=series, channel=channel, frequency_points=frequency_points, power=power, funit=funit, wunit=wunit)
            if (power == power_points[0]): data = series.copy()
            else: data = numpy.concatenate((data, series),axis=1).copy()
        numpy.save(filename, data)
        channel_imaging2(data=data, channel=channel, frequency_points=frequency_points, power_points=power_points, funit=funit, wunit=wunit)
        return data
    
    def timetemp(self, sleeping=1.0):
        def temperature_imageing(temp, time, filename):
            block = ['ADC', 'FPGA', 'Board']
            temp = numpy.array(temp)
            time = numpy.array(time)
            time_axis = time-time[0]
            fig, (ax0, ax1, ax2) = plt.subplots(3, 1, sharex=True)
            ax = [ax0, ax1, ax2]
            for i in range(3):
                for j in range(self.xffts_boardnum):
                    temperature_curve = temp[:,j,i]
                    ax[i].plot(time_axis, temperature_curve, label="Slot%d"%(j+1))
                plt.xlabel("Time [s]")
                plt.ylabel("Temperature [C]")
                plt.title("XFFTS %s Temperature Curve" %block[i])
                plt.axhline(xmin=0)
                plt.grid()
                plt.legend()
            plt.savefig(filename+"XFFTS_%s_Temerature_Curve.png" %block[i])
            plt.close()
            return
        start_time = time.strftime('%Y%m%d_%H%M%S')
        print("Ready...")
        try:
            temp_data = []
            time_data = []
            loopnum = 1
            print("START!")
            while True:
                temp = self.xffts_udp_client.check_all_temperature()[:self.xffts_boardnum]
                time_data.append(time.time())
                temp_data.append(temp)
                print(loopnum, temp)
                loopnum += 1
                time.sleep(sleeping)
        except:
            print("BREAK!")
            end_time = time.strftime('%Y%m%d_%H%M%S')
            temp_data = numpy.array(temp_data)
            time_data = numpy.array(time_data)
        print("SAVING DATA")
        filename = "TimeTemp_%s-%s" %(start_time, end_time)
        numpy.save(filename+"_Temprature", temp_data)
        numpy.save(filename+"_TimeStamp", time_data)
        temperature_imageing(temp=temp_data, time=time_stamp, filename=filename)
        print("END!")
        return [temp_data, time_stamp]
    
    def allan_analyse(self, dt=0.1, allan_chan=None, minsamp=10, sleeping=0):
        def trimming(data, channels):
            data = numpy.array(data)
            totalpower = numpy.mean(data, axis=2)
            output = totalpower.reshape(self.xffts_boardnum)
            if (channels is not None):
                for chan in channels:
                    channel_output = data[:,0,chan]
                    output = numpy.concatenate((output, channel_output), axis=0).copy()
            return output
        def abs_allan_imaging(data, channels, dt, filename):
            data = numpy.array(data)
            data = numpy.array(numpy.split(data, numpy.arange(self.xffts_boardnum,len(data),self.xffts_boardnum), axis=0))
            a,b,c = data.shape
            tag = ["TotalPower"]
            if (channels is not None):
                m = len(channels)
                for k in range(m):
                    channels[k] = str(channels[k])+'ch'
                tag = tag+channels
            time_axis = (numpy.arange(c)+1)*dt
            x = numpy.log10(time_axis)
            for i in range(a):
                for j in range(self.xffts_boardnum):
                    output = data[i,j,:]
                    y = numpy.log10(output)*10
                    plt.plot(x, y)
                    plt.xlabel("Log10(Time) [s]")
                    plt.ylabel("Absolute AllanVariance [dB]")
                    plt.title("XFFTS Slot%d %s Allan Variance" %((j+1),tag[i]))
                    plt.grid()
                    plt.savefig(filename+"_AbsAllan_Slot%d_%s.png" %((j+1),tag[i]))
                    plt.close()
            return
        def rel_allan_imaging(data, channels, dt, filename):
            data = numpy.array(data)
            data = numpy.array(numpy.split(data, numpy.arange(self.xffts_boardnum,len(data),self.xffts_boardnum), axis=0))
            data = numpy.array(data)
            a,b,c = data.shape
            time_axis = (numpy.arange(c)+1)*dt
            x = numpy.log10(time_axis)
            for i in range(self.xffts_boardnum):
                for j in range(a):
                    output = data[j,i,:]
                    y = numpy.log10(output)*10
                    plt.plot(x, y, label=("%dch"%channels[j+1]))
                plt.xlabel("Log10(Time) [s]")
                plt.ylabel("Relational AllanVariance (base=%dch) [dB]"%channels[0])
                plt.title("XFFTS Slot%d Relational AllanVariance (base=%dch)" %((i+1),channels[0]))
                plt.grid()
                plt.savefig(filename+"_RelAllan_Slot%d_base=%dch.png" %((i+1),channels[0]))
                plt.close()
            return
        start_time = time.strftime('%Y%m%d_%H%M%S')
        filename = "AllanAnalyse_%s_dt=%.1fs" %(start_time, dt)
        print("Ready...")
        try:
            output_data = []
            timestamp_data = []
            nans_data = []
            loopnum = 1
            sumnan = 0
            bad_data = 0
            t0 = time.time()
            print("START!")
            while True:
                t1 = time.time()
                spectrum, timestamp = self.xffts_data_client.getspectrum(dt,1,0)
                delay = time.time()-t1
                print(delay)
                gaptime = timestamp[0][0]-t0
                if (0.8*dt<gaptime<1.2*dt): gap=0
                else: gap=1
                t0 = timestamp[0][-1]
                timestamp_data.append(timestamp[0])
                output = trimming(data=spectrum, channels=allan_chan)
                output_data.append(output)
                nanindex = numpy.where(spectrum!=spectrum)
                nans = len(nanindex[0])
                if (nans != 0):
                    bad_data += 1
                    nans_data.append([loopnum-1,nanindex])
                sumnan += nans
                print(loopnum, gap, sumnan, bad_data, nans)
                loopnum += 1
        except:
            print("BREAK!")
        print("SAVING DATA")
        numpy.save(filename+"_TimeStamp", timestamp_data)
        output_data = numpy.swapaxes(output_data,0,1)
        numpy.save(filename+"_OutputData", output_data)
        print("Calculating AllanVariance")
        abs_allan_data = self.allan(data=output_data, minsamp=minsamp)
        numpy.save(filename+"_AbsAllan", abs_allan_data)
        abs_allan_imaging(data=abs_allan_data, channels=allan_chan, dt=dt, filename=filename)
        rel_allan_data = None
        if (allan_chan is not None):
            nchan = len(allan_chan)
            if (nchan >= 2):
                rel_output_data = output_data[2*self.xffts_boardnum:]/numpy.tile(output_data[self.xffts_boardnum:2*self.xffts_boardnum], nchan-1)
                rel_allan_data = self.allan(data=rel_output_data, minsamp=minsamp)
                numpy.save(filename+"_RelAllan_Channel=%s"%allan_chan, rel_allan_data)
                rel_allan_imaging(data=rel_allan_data, channels=allan_chan, dt=dt, filename=filename)
        print("END!")
        return [timestamp_data, output_data, abs_allan_data, rel_allan_data, nans_data]
        
    def allan(self, data, minsamp=2):
        data = numpy.array(data)
        if (len(data.shape) == 1): data = data.reshape(1,len(data))
        a,b = data.shape
        T = numpy.arange(b/minsamp)+1
        allan_series = []
        for t in T:
            x = numpy.array_split(data, numpy.arange(t,b,t), axis=1)
            if (b%t != 0): x = x[:-1]
            x1 = numpy.mean(numpy.array(x), axis=2)
            d = numpy.divide(x1,x1[0,:])
            d1 = d**2
            d2 = numpy.mean(d, axis=0)
            d3 = numpy.mean(d1, axis=0)
            allan_variance = (d3-d2**2)/2
            allan_series.append(allan_variance)
        allan_series = numpy.swapaxes(allan_series,0,1)
        return allan_series
    
    def peak_channel(self, series, num=10):
        series = numpy.array(series)
        if (len(series.shape) != 1):
            print("input 1D array!")
            return
        peak_power = series.max()
        peak_channel = (list(spectrum)).index(peak_power)
        sum, moment = [0,0]
        for i in range(-num,num+1):
            channel = peak_channel+i
            if (0 <= channel <= len(series)-1):
                sum += series[channel]
                moment += series[channel]*channel
        mean_channel = moment/sum
        return [peak_channel, mean_channel]
    
    def show_now(self, filename=None):
        spectrum, timestamp = self.xffts_data_client.getspectrum(0.1, 1, 0)
        nominal_value = spectrum.max()
        if (filename is None):
            filename = "Spectrum_UnixTime=%.2f"%timestamp[0][0]
        for i in range(self.xffts_boardnum):
            x = self.xffts_bandwidth[i]*(numpy.arange(self.xffts_numspecchan[i])+1)/self.xffts_numspecchan[i]
            y = numpy.log10(spectrum[i,0,:]/nominal_value)*10.0
            plt.plot(x, y, label=("Slot%d" %(i+1)))
        plt.xlabel("Frequency [MHz]")
        plt.ylabel("XFFTS Output [dB]")
        plt.title("XFFTS Spectrum")
        plt.legend()
        plt.grid()
        plt.savefig(filename+".png")
        plt.show()
        return

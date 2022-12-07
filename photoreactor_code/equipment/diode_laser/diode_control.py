# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
from mcculw import ul
from mcculw.device_info import DaqDeviceInfo
import datetime as dt
import numpy as np
import time
import re
import os
import pyttsx3
from threading import Thread, Timer


# Sets path when file is imported
package_dir = os.path.dirname(os.path.abspath(__file__))
calibration_path = os.path.join(package_dir, 'diode_calibration.txt')

# # Initiate a voice control object to send alert messages
# voice_control = pyttsx3.init()
# voice_control.setProperty('volume', 1.0)
# rate = voice_control.getProperty('rate')
# voice_control.setProperty('rate', rate + 1)


# # This is some code I took off the internet to get control over the speakers
# devices = AudioUtilities.GetSpeakers()
# interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
# volume_control = cast(interface, POINTER(IAudioEndpointVolume))


# def speak(phrase):

#     # Make sure volume is turned up
#     volume_control.SetMute(0, None) # Unmutes and sets Vol in dB -0.0 is 100%
#     volume_control.SetMasterVolumeLevel(-2.0, None)

#     voice_control.setProperty('volume', 1.0)
#     voice_control.say(phrase)
#     voice_control.runAndWait()
#     voice_control.stop()
#     del(voice_control) # Delete because controller bugs on 2nd call
#     voice_control = pyttsx3.init() #init controller

class Diode_Laser():
    def __init__(self):

        # Set public attr
        self.is_busy = False
        self.board_num = 0
        self.memhandle = None
        self.channel = 0
        self.dev_id_list = []
        self._calibration = [0, 0]

        # Set non-public attr
        self._I_max = 2000  # (mA) Max current of current controller
        self._k_mod = self._I_max/10  # mA/V
        self._daq_dev_info = DaqDeviceInfo(self.board_num)

        self._ao_info = self._daq_dev_info.get_ao_info()

        if self._ao_info.is_supported:
            self._ao_range = self._ao_info.supported_ranges[0]
        else:
            print('Warning: Output not supported by DAQ')

        self._ai_info = self._daq_dev_info.get_ai_info()

        if self._ai_info.is_supported:
            self._ai_range = self._ai_info.supported_ranges[0]
        else:
            print('Warning: Input not supported by DAQ')

        # Initialize equipment
        print('Active DAQ device: ', self._daq_dev_info.product_name, ' (',
              self._daq_dev_info.unique_id, ')\n', sep='')
        self.read_calibration()

        # Initiate a voice control object to send alert messages
        self.voice_control = pyttsx3.init()
        self.voice_control.setProperty('volume', 1.0)
        rate = self.voice_control.getProperty('rate')
        self.voice_control.setProperty('rate', rate + 1)


        # This is some code I took off the internet to get control over the speakers
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume_control = cast(interface, POINTER(IAudioEndpointVolume))
        print('made it to set power line')
        print('self.is_busy = ', self.is_busy)
        self.set_power(0)


    # Read Only Attributes
    I_max = property(lambda self: self._I_max)
    k_mod = property(lambda self: self._k_mod)
    daq_dev_info = property(lambda self: self._daq_dev_info)
    ao_info = property(lambda self: self._ao_info)
    ao_range = property(lambda self: self._ao_range)
    ai_info = property(lambda self: self._ai_info)
    ai_range = property(lambda self: self._ai_range)

    def set_power(self, P_set):
        '''Reads in laser power and sends signal to DAQ to match input power.
        The necessary current is sent based on a externally performed
        calibration. Outputs read power, set point, and time to console.
        reads warning messages when changing power'''

        #TODO put check on max power
        self.voice_control.setProperty('volume', 1.0)
        #TODO can i make this try to be int
        self.voice_control.say('Warning: Setting power to %6.2f milliwatts' % P_set)
        self.voice_control.runAndWait()
        self.voice_control.stop()
        #speak('Warning: Setting power to' + str(P_set) + 'milliwatts')
        I_set = self.P_to_I(P_set)  # (mA) Based on calibration
        I_start = self.get_output_current()
        # TODO can i round this to 0 if negative?
        P_start = self.I_to_P(I_start)
        if P_start < 0: I_start = self.P_to_I(0)
        refresh_rate = 20  # 1/min
        ramp_time = (I_set - I_start)/650  # [min] - spans 1300mA in 2 min
        setpoints = np.linspace(I_start, I_set, abs(int(ramp_time*refresh_rate)))
        setpoints = np.append(setpoints, I_set)
        if P_set != 0: print('ramp time = %6.4f minutes' % ramp_time)

        print('going into setpoint loop')

        while self.is_busy:
            time.sleep(0)
        self.is_busy = True

        for I in setpoints:
            # Ramps the current slowly
            Vout = I/self._k_mod  # (V) Voltage output set point
            if (P_set == 0) and self._ao_info.is_supported:
                Vout = 0
                # Convert to 16bit
                Vout_value = ul.from_eng_units(self.board_num, self._ao_range, Vout)
                # Send signal to DAQ Board
                ul.a_out(self.board_num, 0, self._ao_range, Vout_value)
                break

            elif (P_set != 0) and self._ao_info.is_supported:
                # Convert to 16bit
                Vout_value = ul.from_eng_units(self.board_num, self._ao_range, Vout)
                # Send signal to DAQ Board
                ul.a_out(self.board_num, 0, self._ao_range, Vout_value)
                time.sleep(60/refresh_rate)  # wait
                self.P_set = self.I_to_P(I)
                print('Set Point = %7.2f mW / %7.2f mA' % (self.P_set, I))

            else: print('DAQ Write Not Supported')

        self.is_busy = False
        self.P_set = P_set
        print('\n', time.ctime())
        self.print_output()
        print('Set Point = %7.2f mW / %7.2f mA \n' % (self.P_set, I_set))



    def get_output_current(self):
        '''returns the current measured by DAQ'''
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True

        if self._ai_info.is_supported:
            # Get input value into DAQ
            Vin_value = ul.a_in(self.board_num, self.channel, self._ai_range)
            Vin_eng_units_value = ul.to_eng_units(self.board_num,
                                                  self._ai_range, Vin_value)
            # Convert to relevant output numbers
            V = Vin_eng_units_value
            I = round(V*self._k_mod, 3)
        else:
            print('DAQ Read Not Supported')
            I = 0

        self.is_busy = False
        return(abs(I))

    def get_output_power(self):
        """
        Returns the calculated output power from
        current measured and saved calibration

        Returns
        -------
        P : Power [mW] rounded to 3 decimal points

        """
        I = self.get_output_current()
        P = round(self.I_to_P(I), 3)
        return(P)

    def print_output(self):
        '''prints the output current and power to console'''
        I = self.get_output_current()
        P = self.get_output_power()
        print('Measured Laser output = %7.2f mW / %7.2f mA' % (P, I))

    def I_to_P(self, I):
        """
        converts a current to power based on read calibration

        Parameters
        ----------
        I : current you'd like to convert [mA]

        Returns
        -------
        P : Power [mW]

        """
        m = self._calibration[0]
        b = self._calibration[1]
        P = I*m+b
        return(P)

    def P_to_I(self, P):
        """
        converts a power to current based on read calibration

        Parameters
        ----------
        P : Power you'd like to convert [mW]

        Returns
        -------
        I : current [mA]

        """
        m = self._calibration[0]
        b = self._calibration[1]
        I = (P-b)/m  # (mA) Based on calibration
        return(I)


    def shut_down(self):
        '''Sets power of laser to 0'''
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True
        Vout = 0  # (V) Voltage output set point
        # Convert to 16bit
        Vout_value = ul.from_eng_units(self.board_num, self._ao_range, Vout)
        # Send signal to DAQ Board
        ul.a_out(self.board_num, 0, self._ao_range, Vout_value)
        self.is_busy = False
        print('Finished')

    def update_calibration(self, slope, intercept):
        '''takes in new calibration data and updates calibration file,
        updates class properties'''
        # open and write to calibration file
        with open(calibration_path, 'r+') as old_cal_file:
            new_cal_file = []

            for line in old_cal_file:  # read values after '=' line by line
                if re.search('m = ', line):
                    line = ('m = ' + str(slope) + ' \n')
                elif re.search('b = ', line):
                    line = ('b = ' + str(intercept) + ' \n')
                elif re.search('date = ', line):
                    line = ('date = ' + dt.date.today().strftime('%Y-%m-%d') + '\n')

                new_cal_file += line

            old_cal_file.seek(0)  # Starting from beginning line
            old_cal_file.writelines(new_cal_file)

    def read_calibration(self):
        '''Reads calibration file stored in module directory, updates internal
        properties accordingly'''
        with open(calibration_path, 'r') as calibration:

            for line in calibration:  # read values after '=' line by line
                if re.search('m = ', line):
                    self._calibration[0] = float(
                        line.split('=')[-1].strip(' \n'))
                elif re.search('b = ', line):
                    self._calibration[1] = float(
                        line.split('=')[-1].strip(' \n'))
                elif re.search('date = ', line):
                    print('Last laser calibration was:')
                    print(line)
            print(
                f'Power = {self._calibration[0]}*Current + {self._calibration[1]}\n')

    def time_warning(self, time_left):
        '''Enter time in minutes until activation of laser,
        read outs warning message'''
        # Consider upgrading this to use asyncio or threading.Timer and have
        # the code put out 5 4 3 2 1 minute warnings on a seperate thread
        # Unmutes and sets Vol in dB -0.0 is 100%
        self.volume_control.SetMute(0, None)
        self.voice_control.say(
            f'Warning: Diode laser will automatically engage in {time_left} minutes')
        self.voice_control.runAndWait()

    def set_current(self, I_set):
        '''Sets current output of controller. Use this only when running
        calibration reads warning messages when changing power'''
        while self.is_busy:
            time.sleep(0)
        self.is_busy = True
        Vout = I_set/self._k_mod  # (V) Voltage output set point
        print(I_set)
        print(Vout)
        # Convert to 16bit
        Vout_value = ul.from_eng_units(self.board_num, self._ao_range, Vout)

        # Send signal to DAQ Board
        ul.a_out(self.board_num, 0, self._ao_range, Vout_value)
        Vin_value = ul.a_in(self.board_num, self.channel, self._ai_range)
        Vin_eng_units_value = ul.to_eng_units(self.board_num,
                                              self._ai_range, Vin_value)

        self.print_output()
        print(time.ctime())
        # Unmutes and sets Vol in dB -0.0 is 100%
        self.volume_control.SetMute(0, None)
        self.volume_control.SetMasterVolumeLevel(-2.0, None)
        self.voice_control.say('Warning: Setting current to %6.2f milliamps' % I_set)
        self.voice_control.runAndWait()
        self.is_busy = False

    def start_logger(self, log_frequency=0.1, save_path=None):
        '''starts the data log function to record the laser set point at
        log_frequency intervals (seconds). Takes an optional arugment of the
        desired save path. If none is entered the log gets saved in the driver
        directory. auto increments file name'''
        if save_path is None: # if savepath is unspecified, saves in cwd
            save_path = os.path.join(os.getcwd(),
                                     dt.date.today().strftime('%Y%m%d')+'laser_log.txt')
        while os.path.isfile(save_path): # checks if log w/ default name exists
            m = 1
            save_path = save_path.removesuffix('.txt')
            if re.findall(r'\d+$', save_path): # checks if save_path has number at end
                m += int(re.findall(r'\d+$', save_path)[-1])
            # append number and .txt to filename, then check if name still exists
            save_path = re.split(r'\d+$',save_path)[0]+str(m)
            save_path = save_path+'.txt'

        self.save_path = save_path # assign local pathname to class attribute
        self.timer = RepeatTimer(log_frequency, self.log_power) # create update thread
        self.timer.start()

    def log_power(self):
        '''appends the date at current power setpoint to the outputlog'''
        with open(self.save_path, 'a') as output_log:
            entry = ('%s, %6.2f \n' % (dt.datetime.now(), self.P_set))
            output_log.write(entry)


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

if __name__ == "__main__":
    laser_controller = Diode_Laser()
    #laser_controller.start_logger()
    # laser_controller.set_power(200)
    # time.sleep(3)
    # laser_controller.timer.cancel()
    # laser_controller.time_warning(round(0.5/60))
    # laser_controller.set_power(0)
    # time.sleep(10)
    # laser_controller.set_power(0)
    # laser_controller.shut_down()

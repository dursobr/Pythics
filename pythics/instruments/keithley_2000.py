#
#  Copyright 2008, 2009 Brian R. D'Urso
#
#  This file is part of Python Instrument Control System, also known as Pythics.
#
#  Pythics is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pythics is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Pythics.  If not, see <http://www.gnu.org/licenses/>.
#

# Interface class for Keithley 2000 Multimeter

import visa
import pythics.libinstrument


#
# OLD KEITHLEY2000 DRIVER
#
class Keithley2000(visa.GpibInstrument):
    def __init__(self, *args, **kwargs):
        visa.GpibInstrument.__init__(self, *args, **kwargs)
        
    def Configure(self, **settings):
        self.scan = False
        #self.write('*RST')
        if settings['function'].lower() == 'voltage:dc':
            self.write(":sense:function 'voltage:dc'")
            # measurement range
            if 'range' in settings:
                v = settings['range']
                if v == 'auto':
                    self.write(':sense:voltage:DC:range:auto on')
                else:
                    self.write(':sense:voltage:DC:range:upper ' + str(v))
            # measurement integration line cycles
            if 'n_powerline_cycles' in settings:
                v = settings['n_powerline_cycles']
                # should be a float between 0.01 and 10
                self.write(':sense:voltage:DC:nplcycles ' + str(v))
                self.npl_cycles = v
            else:
                self.write(':sense:voltage:DC:nplcycles 1')                
                self.npl_cycles = 1.0
            # measurement filter
            if 'filter' in settings:
                v = settings['filter']
                if v == 'repeat':
                    self.write(':sense:voltage:DC:average:state 1')
                    self.write(':sense:voltage:DC:average:tcontrol repeat')
                elif v == 'moving':
                    self.write(':sense:voltage:DC:average:state 1')
                    self.write(':sense:voltage:DC:average:tcontrol moving')
                else:
                    # no filter
                    self.write(':sense:voltage:DC:average:state 0')
            # filter time in seconds
            if 'filter_time' in settings:
                v_t = settings['filter_time']
                # integration time is based on power line cycles (60 Hz)
                v = 60.0*v_t/self.npl_cycles
                self.write(':sense:voltage:DC:average:count ' + str(v))
        elif settings['function'].lower() == 'temperature':
            self.write(":sense:function 'temperature'")
            self.write(":unit:temperature C")
            # measurement integration line cycles
            if 'n_powerline_cycles' in settings:
                v = settings['n_powerline_cycles']
                # should be a float between 0.01 and 10
                self.write(':sense:temperature:nplcycles ' + str(v))
                self.npl_cycles = v
            else:
                self.write(':sense:temperature:nplcycles 1')                
                self.npl_cycles = 1.0
            # measurement filter
            if 'filter' in settings:
                v = settings['filter']
                if v == 'repeat':
                    self.write(':sense:temperature:average:state 1')
                    self.write(':sense:temperature:average:tcontrol repeat')
                elif v == 'moving':
                    self.write(':sense:temperature:average:state 1')
                    self.write(':sense:temperature:average:tcontrol moving')
                else:
                    # no filter
                    self.write(':sense:temperature:average:state 0')
            # filter time in seconds
            if 'filter_time' in settings:
                v_t = settings['filter_time']
                # integration time is based on power line cycles (60 Hz)
                v = 60.0*v_t/self.npl_cycles
                self.write(':sense:temperature:average:count ' + str(v))
            # thermocouple type: should be 'J', 'K', or 'T'
            if 'thermocouple_type' in settings:
                v = settings['thermocouple_type']
                self.write(':sense:temperature:tcouple:type ' + str(v))
            # SHOULD BE ABLE TO CONFIGURE THIS
            self.write(':sense:temperature:tcouple:rjunction:rselect real')
        # scanning: should be a tuple of consecutive channels e.g. (1, 2, 3)
        if 'scan' in settings:
            self.scan = True
            v = settings['scan']
            s = '(@' + str(v).strip('()[]') + ')'
            self.write(':initiate:continuous off')
            self.write(':trigger:count ' + str(len(v)))
            self.write(':trigger:source timer')
            self.write(':route:scan ' + s)
            self.write(':trace:points ' + str(len(v)))
            self.write(':trace:feed sense')
            self.write(':trace:feed:control next')
            # time spent at each channel (s)
            if 'scan_step_time' in settings:
                v = settings['scan_step_time']
                self.write(':trigger:timer ' + str(v))
            # start the scan
            self.write(':route:scan:lselect internal')
            self.write(':initiate')

    def Read(self):
        if self.scan == True:
            v = self.ask(':trace:data?')
            self.write(':trace:feed:control next')
            self.write(':initiate')            
            v = v.split(',')
            v = list(map(float, v))
            return v
        else:
            v = self.ask('fetch?')
            return float(v)









#
# Use a Keithley 2000 as a DC voltmeter
#
class Voltmeter(pythics.libinstrument.GPIBInstrument):
    def __init__(self, *args, **kwargs):
        pythics.libinstrument.GPIBInstrument.__init__(self, *args, **kwargs)
        # DO WE NEED TO INITIALIZE SOME DEFAULT VALUES?
        self.write(":sense:function 'voltage:dc'")

    # range property: measurement range
    def __get_range(self):
        # NEEDS WORK 
        return None
    
    def __set_range(self, value): 
        if value == 'auto':
            self.write(':sense:voltage:DC:range:auto on')
        else:
            self.write(':sense:voltage:DC:range:upper ' + str(value))

    range = property(__get_range, __set_range)
    
    # powerline_cycles property: measurement integration line cycles
    def __get_powerline_cycles(self):
        # NEEDS WORK 
        return None
    
    def __set_powerline_cycles(self, value): 
        # should be a float between 0.01 and 10
        self.write(':sense:voltage:DC:nplcycles ' + str(value))
        self._powerline_cycles = value

    powerline_cycles = property(__get_powerline_cycles, __set_powerline_cycles)

    # filter property: measurement filter
    def __get_filter(self):
        # NEEDS WORK 
        return None
    
    def __set_filter(self, value): 
        if value == 'repeat':
            self.write(':sense:voltage:DC:average:state 1')
            self.write(':sense:voltage:DC:average:tcontrol repeat')
        elif value == 'moving':
            self.write(':sense:voltage:DC:average:state 1')
            self.write(':sense:voltage:DC:average:tcontrol moving')
        else:
            # no filter
            self.write(':sense:voltage:DC:average:state 0')
                    
    filter = property(__get_filter, __set_filter)

    # filter_time property: filter time in seconds
    def __get_filter_time(self):
        # NEEDS WORK 
        return None
    
    def __set_filter_time(self, value): 
        # integration time is based on power line cycles (60 Hz)
        v = 60.0*value/self._powerline_cycles
        self.write(':sense:voltage:DC:average:count ' + str(v))
                    
    filter_time = property(__get_filter_time, __set_filter_time)

    # error property
    def __get_error(self): 
        return self.ask('system:error?')
    
    error = property(__get_error)
    
    # voltage property
    def __get_voltage(self): 
        v = self.ask('fetch?')
        return float(v)

    voltage = property(__get_voltage)


#
# Use a Keithley 2000 as a DC Ammeter
#
class Ammeter(pythics.libinstrument.GPIBInstrument):
    def __init__(self, *args, **kwargs):
        pythics.libinstrument.GPIBInstrument.__init__(self, *args, **kwargs)
        # DO WE NEED TO INITIALIZE SOME DEFAULT VALUES?
        self.write(":sense:function 'current:dc'")

    # range property: measurement range
    def __get_range(self):
        # NEEDS WORK 
        return None
    
    def __set_range(self, value): 
        if value == 'auto':
            self.write(':sense:current:DC:range:auto on')
        else:
            self.write(':sense:current:DC:range:upper ' + str(value))

    range = property(__get_range, __set_range)
    
    # powerline_cycles property: measurement integration line cycles
    def __get_powerline_cycles(self):
        # NEEDS WORK 
        return None
    
    def __set_powerline_cycles(self, value): 
        # should be a float between 0.01 and 10
        self.write(':sense:current:DC:nplcycles ' + str(value))
        self._powerline_cycles = value

    powerline_cycles = property(__get_powerline_cycles, __set_powerline_cycles)

    # filter property: measurement filter
    def __get_filter(self):
        # NEEDS WORK 
        return None
    
    def __set_filter(self, value): 
        if value == 'repeat':
            self.write(':sense:current:DC:average:state 1')
            self.write(':sense:current:DC:average:tcontrol repeat')
        elif value == 'moving':
            self.write(':sense:current:DC:average:state 1')
            self.write(':sense:current:DC:average:tcontrol moving')
        else:
            # no filter
            self.write(':sense:current:DC:average:state 0')
                    
    filter = property(__get_filter, __set_filter)

    # filter_time property: filter time in seconds
    def __get_filter_time(self):
        # NEEDS WORK 
        return None
    
    def __set_filter_time(self, value): 
        # integration time is based on power line cycles (60 Hz)
        v = 60.0*value/self._powerline_cycles
        self.write(':sense:current:DC:average:count ' + str(v))
                    
    filter_time = property(__get_filter_time, __set_filter_time)

    # error property
    def __get_error(self): 
        return self.ask('system:error?')
    
    error = property(__get_error)
    
    # current property
    def __get_current(self): 
        i = self.ask('fetch?')
        return float(i)

    current = property(__get_current)

#
# Use a Keithley 2000 as a 2 probe ohmmeter
#
class Ohmmeter(pythics.libinstrument.GPIBInstrument):
    def __init__(self, *args, **kwargs):
        pythics.libinstrument.GPIBInstrument.__init__(self, *args, **kwargs)
        # DO WE NEED TO INITIALIZE SOME DEFAULT VALUES?
        self.write(":sense:function 'resistance'")

    # range property: measurement range
    def __get_range(self):
        # NEEDS WORK 
        return None
    
    def __set_range(self, value): 
        if value == 'auto':
            self.write(':sense:resistance:range:auto on')
        else:
            self.write(':sense:resistance:range:upper ' + str(value))

    range = property(__get_range, __set_range)
    
    # powerline_cycles property: measurement integration line cycles
    def __get_powerline_cycles(self):
        # NEEDS WORK 
        return None
    
    def __set_powerline_cycles(self, value): 
        # should be a float between 0.01 and 10
        self.write(':sense:resistance:nplcycles ' + str(value))
        self._powerline_cycles = value

    powerline_cycles = property(__get_powerline_cycles, __set_powerline_cycles)

    # filter property: measurement filter
    def __get_filter(self):
        # NEEDS WORK 
        return None
    
    def __set_filter(self, value): 
        if value == 'repeat':
            self.write(':sense:resistance:average:state 1')
            self.write(':sense:resistance:average:tcontrol repeat')
        elif value == 'moving':
            self.write(':sense:resistance:average:state 1')
            self.write(':sense:resistance:average:tcontrol moving')
        else:
            # no filter
            self.write(':sense:resistance:average:state 0')
                    
    filter = property(__get_filter, __set_filter)

    # filter_time property: filter time in seconds
    def __get_filter_time(self):
        # NEEDS WORK 
        return None
    
    def __set_filter_time(self, value): 
        # integration time is based on power line cycles (60 Hz)
        v = 60.0*value/self._powerline_cycles
        self.write(':sense:resistance:average:count ' + str(v))
                    
    filter_time = property(__get_filter_time, __set_filter_time)

    # error property
    def __get_error(self): 
        return self.ask('system:error?')
    
    error = property(__get_error)
    
    # resistance property
    def __get_resistance(self): 
        r = self.ask('fetch?')
        return float(r)

    resistance = property(__get_resistance)

#
# Use a Keithley 2000 for scanning through thermocouples
#
class TemperatureScanner(pythics.libinstrument.GPIBInstrument):
    def __init__(self, *args, **kwargs):
        pythics.libinstrument.GPIBInstrument.__init__(self, *args, **kwargs)
        # DO WE NEED TO INITIALIZE SOME DEFAULT VALUES?
        self.write(":sense:function 'temperature'")
        self.write(":unit:temperature C")
        
        # measurement integration line cycles
        v = settings['n_powerline_cycles']
        # should be a float between 0.01 and 10
        self.write(':sense:temperature:nplcycles ' + str(v))
        self.npl_cycles = v
        #else:
        self.write(':sense:temperature:nplcycles 1')                
        self.npl_cycles = 1.0

        # measurement filter
        v = settings['filter']
        if v == 'repeat':
            self.write(':sense:temperature:average:state 1')
            self.write(':sense:temperature:average:tcontrol repeat')
        elif v == 'moving':
            self.write(':sense:temperature:average:state 1')
            self.write(':sense:temperature:average:tcontrol moving')
        else:
            # no filter
            self.write(':sense:temperature:average:state 0')

        # filter time in seconds
        v_t = settings['filter_time']
        # integration time is based on power line cycles (60 Hz)
        v = 60.0*v_t/self.npl_cycles
        self.write(':sense:temperature:average:count ' + str(v))

        # thermocouple type: should be 'J', 'K', or 'T'
        v = settings['thermocouple_type']
        self.write(':sense:temperature:tcouple:type ' + str(v))
        # SHOULD BE ABLE TO CONFIGURE THIS
        self.write(':sense:temperature:tcouple:rjunction:rselect real')

        # scanning: should be a tuple of consecutive channels e.g. (1, 2, 3)
        self.scan = True
        v = settings['scan']
        s = '(@' + str(v).strip('(')
        self.write(':initiate:continuous off')
        self.write(':trigger:count ' + str(len(v)))
        self.write(':trigger:source timer')
        self.write(':route:scan ' + s)
        self.write(':trace:points ' + str(len(v)))
        self.write(':trace:feed sense')
        self.write(':trace:feed:control next')

        # time spent at each channel (s)
        v = settings['scan_step_time']
        self.write(':trigger:timer ' + str(v))

        # start the scan
        self.write(':route:scan:lselect internal')
        self.write(':initiate')
            
    # range property: measurement range
    def __get_range(self):
        # NEEDS WORK 
        return None
    
    def __set_range(self, value): 
        if value == 'auto':
            self.write(':sense:voltage:DC:range:auto on')
        else:
            self.write(':sense:voltage:DC:range:upper ' + str(value))

    range = property(__get_range, __set_range)
    
    # powerline_cycles property: measurement integration line cycles
    def __get_powerline_cycles(self):
        # NEEDS WORK 
        return None
    
    def __set_powerline_cycles(self, value): 
        # should be a float between 0.01 and 10
        self.write(':sense:voltage:DC:nplcycles ' + str(value))
        self._powerline_cycles = value

    powerline_cycles = property(__get_powerline_cycles, __set_powerline_cycles)

    # filter property: measurement filter
    def __get_filter(self):
        # NEEDS WORK 
        return None
    
    def __set_filter(self, value): 
        if value == 'repeat':
            self.write(':sense:voltage:DC:average:state 1')
            self.write(':sense:voltage:DC:average:tcontrol repeat')
        elif value == 'moving':
            self.write(':sense:voltage:DC:average:state 1')
            self.write(':sense:voltage:DC:average:tcontrol moving')
        else:
            # no filter
            self.write(':sense:voltage:DC:average:state 0')
                    
    filter = property(__get_filter, __set_filter)

    # filter_time property: filter time in seconds
    def __get_filter_time(self):
        # NEEDS WORK 
        return None
    
    def __set_filter_time(self, value): 
        # integration time is based on power line cycles (60 Hz)
        v = 60.0*value/self._powerline_cycles
        self.write(':sense:voltage:DC:average:count ' + str(v))
                    
    filter_time = property(__get_filter_time, __set_filter_time)

    # error property
    def __get_error(self): 
        return self.ask('system:error?')
    
    error = property(__get_error)
    
    # voltage property
    def __get_voltage(self): 
        v = self.ask('fetch?')
        return float(v)

    voltage = property(__get_voltage)
    

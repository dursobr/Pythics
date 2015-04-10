#
#  Copyright 2010 - 2012 Brian R. D'Urso
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


import pythics.libinstrument
import visa


class Synthesizer(visa.GpibInstrument):
    #initialization
    def __init__(self, *args, **kwargs):
        visa.GpibInstrument.__init__(self,*args, **kwargs)
        self._frequency = None
        self._amplitude = None
        
    # frequency property
    def __get_frequency(self): 
        return self._frequency

    def __set_frequency(self, value):
        self._frequency = value
        self.write("FREQ "+str(value))
    
    frequency = property(__get_frequency, __set_frequency)

    # amplitude property
    def __get_amplitude(self): 
        return self._amplitude

    def __set_amplitude(self, value):
        self._amplitude = value
        self.write("AMPL "+str(value)+"DB")
    
    amplitude = property(__get_amplitude, __set_amplitude)

    # offset property
    def __get_offset(self): 
        return self._offset

    def __set_offset(self, value):
        self._offset = value
        self.write("OFFS "+str(value))
    
    offset = property(__get_offset, __set_offset)


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

# Last Updated: 1-25-10  Updated By: Elliot Jenner


import pythics.libinstrument
import visa


class SorensenSGA(pythics.libinstrument.GPIBInstrument):

    #initialization
    def __init__(self, loc, **kwargs):
        visa.GpibInstrument.__init__(self, loc)
        #clear the instrument of any chached data
        self.clear()
        self.clear_status()
        self.reset()
        #zero voltage and current as a safety
        self.current = 0
        self.voltage = 0
        
    # current property
    def __get_current(self): 
        return self.ask('measure:current?')

    def __set_current(self, value): 
        self.write('source:current ' + str(value))
    
    current = property(__get_current, __set_current)

    # error property
    def __get_error(self): 
        return self.ask('system:error?')
    
    error = property(__get_error)
    
    # voltage property
    def __get_voltage(self): 
        return self.ask('measure:voltage?')

    def __set_voltage(self, value): 
        self.write('source:voltage ' + str(value))
    
    voltage = property(__get_voltage, __set_voltage)


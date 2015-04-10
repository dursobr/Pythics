#
#  Copyright 2010, 2011 Brian R. D'Urso
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
from pyvisa import vpp43


class Synthesizer(pythics.libinstrument.GPIBInstrument):
    #initialization
    def __init__(self, loc, **kwargs):
        self.board, self.address = loc.split('::')
        self.address_chr = chr(int(self.address)+32)
        session = vpp43.open_default_resource_manager()
        resource_name = vpp43.find_resources(session, self.board)[2]
        vpp43.open(session, resource_name)
        self.board_n = int(self.board.split('B')[1])
        gpib = visa.Gpib(self.board_n)
        vpp43.gpib_send_ifc(gpib.vi)
        vpp43.gpib_control_ren(gpib.vi, 1)
        self._frequency = None
        self._amplitude = None
        
    # frequency property
    def __get_frequency(self): 
        return self._frequency

    def __set_frequency(self, value):
        # example in 488 commands
        # ibsic
        # ibsre 1
        # ibcmd "?@!"
        # ibwrt "F0050000000\n"
        # ibcmd "?"
        self._frequency = value
        s = str(int(round(10*value))).zfill(10)
        gpib = visa.Gpib(self.board_n)
        vpp43.gpib_command(gpib.vi, '?@' + self.address_chr)
        vpp43.write(gpib.vi, 'F' + s + '\n')
        vpp43.gpib_command(gpib.vi, '?')
    
    frequency = property(__get_frequency, __set_frequency)

    # amplitude property
    def __get_amplitude(self): 
        return self._amplitude

    def __set_amplitude(self, value):
        self._amplitude = value
        gpib = visa.Gpib(self.board_n)
        vpp43.gpib_command(gpib.vi, '?@' + self.address_chr)
        vpp43.write(gpib.vi, 'A' + str(int(-value)) + '\n')
        vpp43.gpib_command(gpib.vi, '?')
    
    amplitude = property(__get_amplitude, __set_amplitude)


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


#Interface classes for Zaber T-xxxx motorized stage

import array
import struct
import time
from serial import *


class Chain:
    """Represents the chain of units on a serial interface."""
    def __init__(self):
        self.open = False

    def Open(self, port=0):    
        if self.open:
            raise Exception('chain is already open')
        else:
            self.serial = Serial(port=port,
                                 baudrate=9600,
                                 bytesize=EIGHTBITS,
                                 parity=PARITY_NONE,
                                 stopbits=STOPBITS_ONE,
                                 timeout=100,
                                 xonxoff=0,
                                 rtscts=0,
                                 writeTimeout=None)
            self.open = True
            self.Reset()
            self.Renumber()

    def SendCommand(self, unit, command, data):
        if self.open:
            raw = struct.pack('<BBl', unit, command, data)
            self.serial.write(raw)
        else:
            raise Exception('chain is not open')

    def ReceiveReply(self):
        if self.open:
            raw = self.serial.read(6)
            reply = struct.unpack('<BBl', raw)
            return reply
        else:
            raise Exception('chain is not open')

    def Reset(self):
        if self.open:
            self.serial.flushInput()
            self.serial.flushOutput()
        else:
            raise Exception('chain is not open')

    # should wait then return list of replies
    def Renumber(self):
        if self.open:
            self.SendCommand(0, 2, 0)
            # wait one second
            time.sleep(1)
            # grab all the data waiting
            n = self.serial.inWaiting()
            data_string = self.serial.read(n)
            # convert data to an array
            data_array = array.array('B')
            data_array.fromstring(data_string)
            return(data_array)
        else:
            raise Exception('chain is not open')

    def Close(self):
        if self.open:
            self.serial.close()
            self.open = False
        else:
            raise Exception('chain is not open')
        

class Stage:
    def __init__(self):
        self.open = False

    def Open(self, chain, unit):
        if self.open:
            raise Exception('stage is already open')
        else:
            self.chain = chain
            self.unit = unit
            self.open = True
            self.SetMode()

    def Close(self):
        if self.open:
            self.open = False
        else:
            raise Exception('stage is not open')

    def Reset(self):
        if self.open:
            self.chain.SendCommand(self.unit, 0, 0)
        else:
            raise Exception('stage is not open')

    def Home(self):
        if self.open:
            self.chain.SendCommand(self.unit, 1, 0)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')

    def MoveAbsolute(self, position):
        if self.open:
            self.chain.SendCommand(self.unit, 20, position)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')

    def MoveRelative(self, position):
        if self.open:
            self.chain.SendCommand(self.unit, 21, position)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')
  
    def MoveConstantSpeed(self, speed):
        if self.open:
            self.chain.SendCommand(self.unit, 22, speed)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')

    def Stop(self):
        if self.open:
            self.chain.SendCommand(self.unit, 23, 0)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')

    def RestoreFactoryDefaults(self):
        if self.open:
            self.chain.SendCommand(self.unit, 36, 0)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')

    def SetMicroStepResolution(self, resolution):
        if self.open:
            self.chain.SendCommand(self.unit, 37, resolution)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')

    # should take individual mode options
    def SetMode(self,
                disable_autoreply=False,
                antibacklash=False,
                antisticktion=False,
                disable_potentiometer=False,
                enable_constant_speed_position_tracking=False,
                disable_manual_position_tracking=True,
                enable_logical_channels_mode=False,
                home_status=False):
        mode = (disable_autoreply*1
                + antibacklash*2
                + antisticktion*4
                + disable_potentiometer*8
                + enable_constant_speed_position_tracking*16
                + disable_manual_position_tracking*32
                + enable_logical_channels_mode*64
                + home_status*128)
        if self.open:
            self.chain.SendCommand(self.unit, 40, mode)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')

    def SetTargetVelocity(self, velocity):
        if self.open:
            self.chain.SendCommand(self.unit, 42, velocity)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')

    def SetAcceleration(self, acceleration):
        if self.open:
            self.chain.SendCommand(self.unit, 43, acceleration)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')

    def SetRange(self, range):
        if self.open:
            self.chain.SendCommand(self.unit, 44, range)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')

    def ReturnDeviceID(self):
        if self.open:
            self.chain.SendCommand(self.unit, 50, 0)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')
    
    def ReturnPosition(self):
        if self.open:
            self.chain.SendCommand(self.unit, 60, 0)
            (unit, command, data) = self.chain.ReceiveReply()
            return data
        else:
            raise Exception('stage is not open')
   


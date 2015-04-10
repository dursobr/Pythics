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


#Interface class for Mettler Toledo UMX2 Balance

from serial import *
import time


class Balance:
    def __init__(self):
        self.open = False

    def Open(self, 
            port=0,                 #number of device, numbering starts at zero
            baudrate=9600,          #baudrate
            bytesize=EIGHTBITS,     #number of databits
            parity=PARITY_NONE,     #enable parity checking
            stopbits=STOPBITS_ONE,  #number of stopbits
            timeout=1,              #set a timeout value, None to wait forever
            xonxoff=1,              #enable software flow control
            rtscts=0,               #enable RTS/CTS flow control
            writeTimeout=None):     #set a timeout for writes    
        if self.open:
            raise Exception('balance is already open')
        else:
            self.serial = Serial(port=port, baudrate=baudrate, 
                bytesize=bytesize, parity=parity, stopbits=stopbits, timeout=timeout, 
                xonxoff=xonxoff, rtscts=rtscts, writeTimeout=writeTimeout)
            self.serial.flushInput()
            self.serial.flushOutput()
            self.open = True

    def Reset(self):
        self.serial.flushInput()
        self.serial.flushOutput()
        self.serial.write('@\r\n')
        return(self.serial.readline())

    def SendWeightValueImmediately(self):
        self.serial.write('SI\r\n')
        return(self.ReadSentWeight())

    def SendWeightValueImmediatelyAndRepeat(self):
        self.serial.write('SIR\r\n')

    def ReadSentWeight(self):
        reply = self.serial.readline()
        split_reply = string.split(reply)
        split_reply[2] = float(split_reply[2])
        return(split_reply)

    def StopAndClear(self):
        self.serial.sendBreak()
        time.sleep(1)
        self.serial.flushInput()
        self.serial.flushOutput()

    def Close(self):
        if self.open:
            self.serial.close()
            self.open = False
        else:
            raise Exception('balance is not open')

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

# This device really wants to be talking to hyperterminal. Extreme Kludging required to make it work here. PySerial may be better.

import visa
import pyvisa.vpp43 as vpp43
import re


class iopower8(visa.SerialInstrument):
    #initialization
    def __init__(self,loc):
        visa.SerialInstrument.__init__(self,loc)
        self.term_chars = '\r' #set terminal characters
        self.write('\r\r')
        self.all_off(1)
        
    def on(self, bank, out):
        self.ask("on " + str(bank) + " " + str(out))
        for i in range (1,3):#read buffer into void to prevent issues
            try:
                self.read_raw()
            except(vpp43.visa_exceptions.VisaIOError):
                self.buffer_clear()
                break
        return self.status(bank, out)
                
    def off(self, bank, out):
        self.ask("of " + str(bank) + " " + str(out))
        for i in range (1,3):#read buffer into void to prevent issues
            try:
                self.read_raw()
            except(vpp43.visa_exceptions.VisaIOError):
                self.buffer_clear()
                break
        return self.status(bank, out)
    
    def status(self, bank, port): #enter bank and port # you want to check
        self.ask("st " + str(bank))
        result = 'Error' #send error message regardless
        for i in range (1,13):#all 12 lines need to be read out of the buffer to prevent issues later
            try:
                stuff = self.read()#read the line to a holding string, and dump in void if wrong line to clear buffer
                if len(stuff) and stuff.strip()[0] == '=':
                    break
            except(vpp43.visa_exceptions.VisaIOError):
                break
        for i in range(1,9):
            try:
                stuff = self.read()#read the line to a holding string, and dump in void if wriong line to clear buffer.
                if i == port: #this offset will get you to the line with the relevant port's status
                    result = re.match('(.*?)(ON|OFF)', stuff) #regex to the find the on/off status
                    #convert to boolean
                    if result.group(2) == 'ON':
                        result = True
                    elif result.group(2) =='OFF':
                        result = False
                    else:
                        result = 'ERROR'
            except(vpp43.visa_exceptions.VisaIOError):
                self.buffer_clear()
                break
        return result
    
    def buffer_clear(self): #in case of buffer jamming
        while True:
            try:
                self.read_raw()
            except(vpp43.visa_exceptions.VisaIOError):
                break
                
    def all_on(self, bank):
        self.ask("on " + str(bank) + " 0")
        for i in range (1,3):#read buffer into void to prevent issues
            try:
                hold = self.read_raw()
            except(vpp43.visa_exceptions.VisaIOError):
                self.buffer_clear()
                break
                
    def all_off(self, bank):
        self.ask("of " + str(bank) + " 0")
        for i in range (1,3):#read buffer into void to prevent issues
            try:
                self.read_raw()
            except(vpp43.visa_exceptions.VisaIOError):
                self.buffer_clear()
                break
                
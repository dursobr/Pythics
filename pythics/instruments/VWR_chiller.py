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
#  Module by Elliot Jenner, updated 12-4-09

import visa


class VWRChiller(visa.SerialInstrument):
    #initialization
    #always check system tenperature units. There is no command for remote setting.
    def __init__(self,loc):
        visa.SerialInstrument.__init__(self,loc)
        self.__no_echo()
        
    #the chiller returns ! on a success and nothing on a failure, so we convert it to a boolean
    def __check(self, ans):
        if (ans.replace('\n','') == '!'):
            ans = True
        else:
            ans = False
        return ans
    
    #this command tells the chiller not to echo back commands that are sent to it. can also be used to check if the RS232 bus selection is correct.
    def __no_echo(self):
        stat = self.ask('SE0')
        return self.__check(stat)
        
    #on/off status
    def is_on(self):
        stat = self.ask('RW')
        stat.replace('\n','')
        if (stat == '1'):
            return True
        elif (stat == '0'):
            return False
        else:
            return 'Error'
        
    def start(self):
        stat = self.ask('SO1')
        return self.__check(stat)
        
    def stop(self):
        stat = self.ask('SO0')
        return self.__check(stat)
        
    #temperature set point check and control.
    def __get_temp(self):
        return float(self.ask('RS'))
    
    def __set_temp(self, temp):
        temp = round(temp, 1)
        set = 'SS' + str(temp) #signal must be of the form SSxxx, where xxx is the temp
        stat = self.ask(set)
        return self.__check(stat)
        
    set_temp = property(__get_temp, __set_temp)
    
    #actual device temperature
    def __read_temp(self):
        return float(self.ask('RT'))
    
    temp = property(__read_temp)
    
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
# Last Updated: 5-1-2011  Updated By: Brian D'Urso


import visa
import numpy as npy

import pythics.libinstrument


class PowerSupply(visa.GpibInstrument):
    #initialization
    def __init__(self,*args,**kwargs):
        visa.GpibInstrument.__init__(self,*args, **kwargs)
        self.write('*CLS;*RST')

    def read_volt(self):
        #returns both programmed value and measured value      
        p=self.ask('MEAS:VOLT?')
        return p
     
    def read_current(self):
        p=self.ask('MEAS:CURR?')
        return p
        
    def set_volts(self,x):
        self.write('VOLT '+ x +' V')
        
    def set_current(self,y):
        self.write('CURR '+ y +' A')
        
    def set_overvolt(self,z):
        #sets overvolt and overcurrent protection
        self.write('PROT' + z +';PROT:STAT ON')
        
    def output_on(self):
        self.write("OUTP 1")
        
    def output_off(self):
        self.write("OUTP 0")

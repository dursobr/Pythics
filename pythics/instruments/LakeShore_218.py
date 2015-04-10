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
# Last Updated: 10-7-10  Updated By: Steven Huffman



import visa
import pythics.libinstrument
import numpy as npy

class TemperatureMonitor(visa.GpibInstrument):
    #initialization
    def __init__(self,*args,**kwargs):
        visa.GpibInstrument.__init__(self,*args, **kwargs)

    def read_temps(self):
        #returns the temperature reading at the desired probe number. if probe num= 0 then returns all sensor readings        
        p=self.ask("KRDG?0")
        p=p.split(',')
        x =[]
        for i in range(len(p)):
            x.append(float(p[i]))
        return x
        
    def read_resist(self):
        #returns the resistance reading at the desired probe number. if probe num= 0 then returns all sensor readings        
        p=self.ask("SRDG?0")
        p=p.split(',')
        x =[]
        for i in range(len(p)):
            x.append(float(p[i]))
        return x
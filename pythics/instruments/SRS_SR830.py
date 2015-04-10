#
#  Copyright 2010, 2011 Brian R. D'Urso
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

import visa


class LockInAmplifier(visa.GpibInstrument):
    #initialization
    def __init__(self,*args,**kwargs):
        visa.GpibInstrument.__init__(self,*args, **kwargs)

    def read_x(self):
        p = self.ask("OUTP? 1")
        return float(p)
     
    def read_y(self):
        p = self.ask("OUTP? 2")
        return float(p)
        
    def read_phase(self):
        p = self.ask("PHAS?")
        return p
        
    def set_sample_rate(self, rate):
        # rate is a value from 0 (62.5mHz) to 13 (512Hz) or 14 for Trigger
        self.write('SRAT '+str(rate))
        
    def trigger(self):
        self.write('TRIG')
        
    def reset_buffer(self):
        self.write('REST')
        
    def read_xy(self):
        xy = self.ask('SNAP? 1,2')
        a = xy.split(',')
        return float(a[0]), float(a[1])
        
    def read_12(self):
        xy = self.ask('SNAP? 10,11')
        a = xy.split(',')
        return float(a[0]), float(a[1])
        
    sensitivity_list = ['2 nV/fA', '5 nV/fA', '10 nV/fA', '20 nV/fA', '50 nV/fA', '100 nV/fA', '200 nV/fA', '500 nV/fA',
               '1 uV/pA', '2 uV/pA', '5 uV/pA', '10 uV/pA', '20 uV/pA', '50 uV/pA', '100 uV/pA', '200 uV/pA', '500 uV/pA',
               '1 mV/nA', '2 mV/nA', '5 mV/nA', '10 mV/nA', '20 mV/nA', '50 mV/nA', '100 mV/nA', '200 mV/nA', '500 mV/nA',
               '1 V/uA']

    def set_sensitivity(self, sensitivity):
        s = self.sensitivity_list.index(sensitivity)
        self.write('SENS ' + str(s))
        
    time_constant_list = ['10 us', '30 us', '100 us', '300 us', 
                '1 ms', '3 ms', '10 ms', '30 ms', '100 ms', '300 ms', 
                '1 s', '3 s', '10 s', '30 s', '100 s', '300 s', 
                '1 ks', '3 ks', '10 ks', '30 ks']

    def set_time_constant(self, time_constant):
        tc = self.time_constant_list.index(time_constant)        
        self.write('OFLT ' + str(tc))

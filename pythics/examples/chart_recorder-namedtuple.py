# -*- coding: utf-8 -*-
#
#  Copyright 2012 - 2014 Brian R. D'Urso
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

#
# load libraries
#
from collections import namedtuple

import numpy as np

from pythics.lib import GrowableArray



def kwargs_to_namedtuple(func):
    def wrapper(**kwargs):
        controls = namedtuple('Controls', kwargs.keys())(**kwargs)
        return func(controls)
    return wrapper


def namedtuple_to_kwargs(func):
    def wrapper(controls):
        return func(**(controls._todict()))
    return wrapper


#
# private data shared among functions
#
class Private(object):
    pass

private = Private()


#
# functions
#
#def initialize(**kwargs):
@kwargs_to_namedtuple
def initialize(C):    
    # store data in a GrawableArray so we can efficiently append to it
    private.data = GrowableArray(cols=5, length=1000)
    # setup the plot
    C.data_chart.curves_per_plot = [1, 1, 2]
    C.data_chart.set_plot_properties(0, title='Recorded Voltages', y_label='V1 (V)')
    C.data_chart.set_plot_properties(1, y_label='V2 (V)')
    C.data_chart.set_plot_properties(2, x_label='time (s)', y_label='V3 and V4 (V)')
    C.data_chart.set_curve_properties(0, line_color='red', line_width=2)
    C.data_chart.set_curve_properties(1, line_color='green', line_width=2)
    C.data_chart.set_curve_properties(2, line_color='orange', line_width=1)
    C.data_chart.set_curve_properties(3, line_color='blue', line_width=1)


#def open_close_instruments(**kwargs):
@kwargs_to_namedtuple
def open_close_instruments(C):
    # use this for setting up hardware, if needed
    if C.open_close.value:
        # open instruments
        pass
    else:
        # check that we are not running before closing instruments
        if C.start_stop.value:
            C.error_dialog.message = 'Stop before closing instruments.'
            C.error_dialog.open()
            C.open_close.value = True
            return
        # close instruments
        pass


#def run(**kwargs):
@kwargs_to_namedtuple
def run(C):
    # check that the instruments are open before starting
    if not C.open_close.value:
        C.error_dialog.message = 'Open instruments before starting.'
        C.error_dialog.open()
        return
    private.data.clear()
    C.data_chart.clear_data()
    if C.dwell_time.value < 0.1:
        # use fast plotting (hidden axes) for data taken faster than 10 Hz
        #  you may want to change this depending on the speed of your computer
        C.data_chart.fast = True
    t = 0.0
    while(C.start_stop.value):
        # read and show voltages
        new_y1 = 5*np.random.rand()
        new_y2 = 4*np.random.rand()
        new_y3 = 2*np.random.rand()
        new_y4 = 3*np.random.rand()
        C.voltage_1.value = new_y1
        C.voltage_2.value = new_y2
        C.voltage_3.value = new_y3
        C.voltage_4.value = new_y4
        new_data = np.array([t, new_y1, new_y2, new_y3, new_y4])
        private.data.append(new_data)
        C.data_chart.append_data(new_data)
        dt = C.dwell_time.value
        t += dt
        yield dt
    # turn axes drawing back on
    C.data_chart.fast = False
    

#def save_data(**kwargs):
@kwargs_to_namedtuple
def save_data(C):
    np.savetxt(C.data_filename.value, private.data, 
                  fmt='%.18e', 
                  delimiter=' ', 
                  newline='\n', 
                  header='x y1 y2 y3 y4', 
                  footer='', 
                  comments='# ')


#def load_data(**kwargs):
@kwargs_to_namedtuple
def load_data(C):
    a = np.loadtxt(C.data_filename.value, 
                   dtype='float', 
                   comments='#', 
                   ndmin=2)
    private.data.clear()
    private.data.append(a)
    C.data_chart.set_data(private.data)


#def terminate(**kwargs):
@kwargs_to_namedtuple
def terminate(C):
    # called when the vi is closed
    pass
    
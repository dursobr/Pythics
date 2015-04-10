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
import numpy as np

from pythics.lib import GrowableArray


#
# private data shared among functions
#
class Private(object):
    pass

private = Private()


#
# functions
#
def initialize(data_chart, **kwargs):
    # store data in a GrawableArray so we can efficiently append to it
    private.data = GrowableArray(cols=5, length=1000)
    # setup the plot
    data_chart.curves_per_plot = [1, 1, 2]
    data_chart.set_plot_properties(0, title='Recorded Voltages', y_label='V1 (V)')
    data_chart.set_plot_properties(1, y_label='V2 (V)')
    data_chart.set_plot_properties(2, x_label='time (s)', y_label='V3 and V4 (V)')
    data_chart.set_curve_properties(0, line_color='red', line_width=2)
    data_chart.set_curve_properties(1, line_color='green', line_width=2)
    data_chart.set_curve_properties(2, line_color='orange', line_width=1)
    data_chart.set_curve_properties(3, line_color='blue', line_width=1)


def open_close_instruments(open_close, start_stop, error_dialog, **kwargs):
    # use this for setting up hardware, if needed
    if open_close.value:
        # open instruments
        pass
    else:
        # check that we are not running before closing instruments
        if start_stop.value:
            error_dialog.message = 'Stop before closing instruments.'
            error_dialog.open()
            open_close.value = True
            return
        # close instruments
        pass


def run(voltage_1, voltage_2, voltage_3, voltage_4, data_chart, dwell_time, 
        start_stop, error_dialog, open_close, **kwargs):
    # check that the instruments are open before starting
    if not open_close.value:
        error_dialog.message = 'Open instruments before starting.'
        error_dialog.open()
        return
    private.data.clear()
    data_chart.clear_data()
    if dwell_time.value < 0.1:
        # use fast plotting (hidden axes) for data taken faster than 10 Hz
        #  you may want to change this depending on the speed of your computer
        data_chart.fast = True
    t = 0.0
    while(start_stop.value):
        # read and show voltages
        new_y1 = 5*np.random.rand()
        new_y2 = 4*np.random.rand()
        new_y3 = 2*np.random.rand()
        new_y4 = 3*np.random.rand()
        voltage_1.value = new_y1
        voltage_2.value = new_y2
        voltage_3.value = new_y3
        voltage_4.value = new_y4
        new_data = np.array([t, new_y1, new_y2, new_y3, new_y4])
        private.data.append(new_data)
        data_chart.append_data(new_data)
        dt = dwell_time.value
        t += dt
        yield dt
    # turn axes drawing back on
    data_chart.fast = False
    

def save_data(data_filename, **kwargs):
    np.savetxt(data_filename.value, private.data, 
                  fmt='%.18e', 
                  delimiter=' ', 
                  newline='\n', 
                  header='x y1 y2 y3 y4', 
                  footer='', 
                  comments='# ')


def load_data(data_chart, data_filename, **kwargs):
    a = np.loadtxt(data_filename.value, 
                   dtype='float', 
                   comments='#', 
                   ndmin=2)
    private.data.clear()
    private.data.append(a)
    data_chart.set_data(private.data)


def terminate(**kwargs):
    # called when the vi is closed
    pass
    
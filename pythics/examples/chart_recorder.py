# -*- coding: utf-8 -*-
#
#  Copyright 2012 - 2019 Brian R. D'Urso
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
import logging
import time

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
def initialize(log_text_box, data_chart, **kwargs):
    # setup the logger and log display box
    # examples of how to use:
    #    private.logger.debug('this is a debug message')
    #    private.logger.info('this is an info message')
    #    private.logger.warning('this is a warning message')
    #    private.logger.error('this is an error message')
    #    private.logger.critical('this is a critical error message')
    #    private.logger.exception('this is an exception')
    private.logger = logging.getLogger('log')
    #private.logger.setLevel(logging.DEBUG)
    private.logger.setLevel(logging.INFO)
    sh = logging.StreamHandler(log_text_box)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    private.logger.addHandler(sh)
    # store data in a GrawableArray so we can efficiently append to it
    private.data = GrowableArray(cols=2, length=1000)
    # setup the plot
    data_chart.curves_per_plot = [1]
    data_chart.set_plot_properties(0, title='Recorded Voltages', x_label='time (s)', y_label='$V_1$ (V)')
    data_chart.set_curve_properties(0, line_color='red', line_width=2)
    private.logger.debug('initialize complete')


def open_close_instruments(main, open_close, start_stop, **kwargs):
    try:
        # use this for setting up hardware, if needed
        if open_close.value:
            private.logger.debug('opening instruments')
            # open instruments
            pass
            private.logger.info('instruments opened')
        else:
            # check that we are not running before closing instruments
            if start_stop.value:
                main.open_message_dialog('Error', 'Stop before closing instruments.', severity='critical')
                open_close.value = True
                return
            private.logger.debug('closing instruments')
            # close instruments
            pass
            private.logger.info('instruments closed')
    except:
        private.logger.exception('execution stopped due to an exception')


def run(main, time_display, voltage_1_display, data_chart, dwell_time, 
        start_stop, open_close, **kwargs):
    try:
        # check that the instruments are open before starting
        if not open_close.value:
            main.open_message_dialog('Error', 'Open instruments before starting.', severity='critical')
            return
        private.logger.info('starting data acquisition')
        private.data.clear()
        data_chart.clear_data()
        if dwell_time.value < 0.01:
            # use fast plotting (hidden axes) for data taken faster than 10 Hz
            #  you may want to change this depending on the speed of your computer
            data_chart.fast = True
        t0 = time.time()
        while(start_stop.value):
            private.logger.debug('acquiring data')
            # read and show voltages
            new_t = time.time() - t0
            time_display.value = new_t
            new_y1 = 5*np.random.rand()
            voltage_1_display.value = new_y1
            new_data = np.array([new_t, new_y1])
            private.data.append(new_data)
            data_chart.append_data(new_data)
            yield dwell_time.value
        private.logger.info('stopping data acquisition')
        # turn axes drawing back on
        data_chart.fast = False
    except:
        private.logger.exception('execution stopped due to an exception')
    

def save_data(save_data_filename, **kwargs):
    try:
        np.savetxt(save_data_filename.value, private.data, 
                      fmt='%.18e', 
                      delimiter=' ', 
                      newline='\n', 
                      header='t V_1', 
                      footer='', 
                      comments='# ')
    except:
        private.logger.exception('save stopped due to an exception')


def load_data(data_chart, load_data_filename, **kwargs):
    try:
        a = np.loadtxt(load_data_filename.value,
                       dtype='float',
                       comments='#', ndmin=2)
        private.data.clear()
        private.data.append(a)
        data_chart.set_data(private.data)
    except:
        private.logger.exception('load stopped due to an exception')

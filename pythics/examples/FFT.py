# -*- coding: utf-8 -*-
#
#  Copyright 2012 - 2013 Brian R. D'Urso
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
import math
import numpy as np


#
# basic functionality: initialize, start, stop, clear
#
class Empty(object):
    pass

data = Empty()


def initialize(shell, **kwargs):
    d = kwargs.copy()
    d['data'] = data
    shell.interact(d)
    clear(**kwargs)


def clear(messages, plot_1, plot_2, **kwargs):
    plot_1.clear()
    plot_2.clear()
    messages.clear()
    plot_1.set_plot_properties(
        title='Time Domain',
        x_label='t',
        y_label='f(t)',
        aspect_ratio='auto')
    plot_2.set_plot_properties(
        title='Frequency Domain',
        x_label='f',
        y_label='f(f)',
        y_scale='linear',
        #y_scale='log',
        aspect_ratio='auto')
    plot_1.new_curve('data_t', line_color='blue', 
                     marker_style='o', marker_color='blue', marker_width=3)
    plot_2.new_curve('data_f-real', line_color='green', 
                     marker_style='o', marker_color='green', marker_width=3)
    plot_2.new_curve('data_f-imag', line_color='red', 
                     marker_style='o', marker_color='red', marker_width=3)
    plot_2.new_curve('data_f-abs', line_color='green', 
                     marker_style='o', marker_color='green', marker_width=3)


def f(t, s):
    return eval(s)


def run(function, range_min, range_max, N, messages, plot_1, plot_2, **kwargs):
    N_steps = N.value
    ts = np.linspace(range_min.value, range_max.value, N_steps)
    f_string = function.value
    ys = np.zeros(len(ts))
    for i in range(N_steps):
        ys[i] = f(ts[i], f_string)
    global data 
    data.value = ys
    plot_1.set_data('data_t', np.column_stack([ts, ys]))
    fts = np.fft.rfft(ys)
    fts /= len(fts)
    fs = np.arange(len(fts))/float(ts[-1]-ts[0])
    # PLOT real()
    plot_2.set_data('data_f-real', np.column_stack([fs, np.real(fts)]))
    # PLOT imag()
    plot_2.set_data('data_f-imag', np.column_stack([fs, np.imag(fts)]))
    # PLOT abs() or log10(abs())
    #plot_2.set_data('data_f-abs', np.column_stack([fs, np.abs(fts)]))

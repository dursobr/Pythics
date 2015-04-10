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

import numpy as np
from pythics.lib import CircularArray


def initialize_shell(shell, **kwargs):
    shell.interact(kwargs.copy())
    clear(**kwargs)


def clear(plot_1, plot_2, plot_3, plot_4, messages, **kwargs):
    plot_1.clear()
    plot_2.clear()
    plot_3.clear()
    plot_4.clear()
    messages.clear()
    plot_1.set_plot_properties(
        title='String',
        x_label='x',
        y_label='y',
        x_scale='linear',
        y_scale='linear',
        y_limits=(-1.1, 1.1),
        aspect_ratio='auto')
    plot_2.set_plot_properties(
        title='FFT of y(x)',
        x_label='spatial f',
        y_label='A(f)',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')
    plot_3.set_plot_properties(
        title='Displacement of One Point',
        x_label='t',
        y_label='y',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')
    plot_4.set_plot_properties(
        title='FFT of y(t) at One Point',
        x_label='f',
        y_label='A(f)',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')
    plot_1.new_curve('xy', animated=True, line_style='-', line_color='green',
                     marker_style='+', marker_edge_color='green', marker_width=3)
    plot_2.new_curve('xf', animated=True, line_style='-', line_color='blue',
                     marker_style='+', marker_edge_color='blue', marker_width=3)
    plot_3.new_curve('ty', animated=True, line_style='-', line_color='red',
                     marker_style='+', marker_edge_color='red', marker_width=3)
    plot_4.new_curve('tf', animated=True, line_style='-', line_color='red',
                     marker_style='+', marker_edge_color='red', marker_width=3)


def run(w_L, w_N, w_dt, w_pluck, w_monitor, w_N_tfft, w_N_tfft_display, w_drag, 
        stop, messages, plot_1, plot_2, plot_3, plot_4, **kwargs):
    N = w_N.value
    L = w_L.value
    dt = w_dt.value
    c = 1.0
    pluck = w_pluck.value
    monitor = w_monitor.value
    N_tfft = w_N_tfft.value
    N_tfft_display = w_N_tfft_display.value
    drag = w_drag.value
    messages.write('\n=== WAVES ===============================\n')
    # spatial domain data and initial condition
    N_pluck = int(round(N*pluck))
    data_x = np.linspace(0.0, L, N+1)
    ratio = (dt*c/(data_x[1]-data_x[0]))**2
    data_y = np.zeros(N+1, float)
    data_y[0:N_pluck+1] = np.linspace(0.0, 1.0, N_pluck+1)
    data_y[N_pluck:] = np.linspace(1.0, 0.0, N-N_pluck+1)
    data_y[N_pluck] = 1
    data_y[-1] = 0
    plot_1.set_data('xy', np.column_stack((data_x, data_y)))
    last_data_y = data_y.copy()
    last_last_data_y = data_y.copy()
    # initialize last_data_y: need to take a 'half step'
    last_data_y[1:-1] = last_last_data_y[1:-1] \
        +0.5*ratio*(last_last_data_y[2:]+last_last_data_y[0:-2]-2*last_last_data_y[1:-1])
    # spatial domain fft
    spatial_fft_data_y = np.zeros(2*N, np.float)
    spatial_fft_data_y[0:N+1] = data_y[:]
    spatial_fft_data_y[N+1:] = -data_y[-2:0:-1]
    spatial_fft_y = np.fft.rfft(spatial_fft_data_y)
    spatial_fft_x = np.arange(spatial_fft_y.shape[0])
    plot_2.set_data('xf', np.column_stack((spatial_fft_x, abs(spatial_fft_y))))
    # time domain data stored in RingBuffer
    N_monitor = int(round(N*monitor))
    data_yt = CircularArray(length=N_tfft, cols=2)
    n = 0
    while(True):
        data_y[1:-1] = 2*last_data_y[1:-1]-last_last_data_y[1:-1] \
            +ratio*(last_data_y[2:]+last_data_y[0:-2]-2*last_data_y[1:-1]) \
            -drag*(last_data_y[1:-1]-last_last_data_y[1:-1])
        data_yt.append(np.array([n*dt, data_y[N_monitor]]))
        if n % 4 == 0:
            plot_1.set_data('xy', np.column_stack((data_x, data_y)))
            spatial_fft_data_y[0:N+1] = data_y[:]
            spatial_fft_data_y[N+1:] = -data_y[-2:0:-1]
            spatial_fft_y = np.fft.rfft(spatial_fft_data_y)
            plot_2.set_data('xf', np.column_stack((spatial_fft_x, abs(spatial_fft_y))))
            plot_3.set_data('ty', data_yt[:])
            # time domain fft
            time_fft_y = np.fft.rfft(data_yt[:,1])
            time_fft_x = np.linspace(0.0, 0.5/dt, time_fft_y.shape[0])
            plot_4.set_data('tf', np.column_stack((time_fft_x[0:N_tfft_display], abs(time_fft_y[0:N_tfft_display]))))
        n += 1
        temp = last_last_data_y
        last_last_data_y = last_data_y
        last_data_y = data_y
        data_y = temp
        if stop.value:
            break
    # reset the stop button in case it was pushed
    stop.value = False
    messages.write('Done.\n')

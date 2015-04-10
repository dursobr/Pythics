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

def initialize_shell(shell, **kwargs):
    shell.interact(kwargs.copy())
    clear(**kwargs)

data_T = None
data_x = None

def clear(plot_1, messages, **kwargs):
    plot_1.clear()
    messages.clear()
    plot_1.set_plot_properties(
        title='Temperature Distribution',
        x_label='x',
        y_label='T',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')
    plot_1.new_curve('T', animated=True, line_style='-', line_color='red',
                     marker_style='+', marker_edge_color='red', marker_width=5)


#------------------------------------------------------------------------------
#  Edit the functions below to accomplish the desired task. Please begin each 
#  run function by writing the question number to the ouput messages box.
#
#  You may need to write additional functions to complete the assignment, and
#  all code you write should be included below.
#------------------------------------------------------------------------------

def run(hf_dt, hf_time_steps, hf_N, hf_initial_T, hf_left_T, hf_right_T,
        stop, messages, plot_1, **kwargs):
    dt = hf_dt.value
    steps = hf_time_steps.value
    messages.write('\n=== HEAT FLOW =========================\n')
    data_x = np.arange(hf_N.value)
    data_T = np.ones(hf_N.value)*hf_initial_T.value
    data_T[0] = hf_left_T.value
    data_T[-1] = hf_right_T.value
    plot_1.set_data('T', np.column_stack((data_x, data_T)), rescale=True)
    for n in range(steps):
        data_T[1:-1] += dt*(data_T[0:-2] + data_T[2:] - 2*data_T[1:-1])
        if n % 10 == 0:
            plot_1.set_data('T', np.column_stack((data_x, data_T)))
        if stop.value: break
    # reset the stop button in case it was pushed
    stop.value = False
    messages.write('Done.\n')

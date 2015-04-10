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

data = None

def clear(plot_1, messages, **kwargs):
    plot_1.clear()
    messages.clear()


#------------------------------------------------------------------------------
#  Edit the functions below to accomplish the desired task. Please begin each 
#  run function by writing the question number to the ouput messages box.
#
#  You may need to write additional functions to complete the assignment, and
#  all code you write should be included below.
#------------------------------------------------------------------------------

def run(laplace_Nx, laplace_Ny, laplace_tolerance, laplace_over_relaxation,
        laplace_source_1_x, laplace_source_1_y, laplace_source_1_value,
        laplace_source_2_x, laplace_source_2_y, laplace_source_2_value,
        stop, messages, plot_1, **kwargs):
    tolerance = laplace_tolerance.value
    ovr = laplace_over_relaxation.value
    source_1_x = laplace_source_1_x.value
    source_1_y = laplace_source_1_y.value
    source_1_value = laplace_source_1_value.value
    source_2_x = laplace_source_2_x.value
    source_2_y = laplace_source_2_y.value
    source_2_value = laplace_source_2_value.value
    messages.write('\n=== LAPLACE =========================\n')
    plot_1.set_plot_properties(
        title='Temperature Distribution',
        x_label='x',
        y_label='y',
        x_scale='linear',
        y_scale='linear',
        tight_autoscale=True,
        aspect_ratio='equal')
    plot_1.new_image('T', animated=False, interpolation='nearest')
    data = np.zeros((laplace_Nx.value, laplace_Ny.value))
    data[0,:] = 0
    data[-1,:] = 0
    data[:,0] = 0
    data[:,-1] = 0
    data[source_1_x, source_1_y] = source_1_value
    data[source_2_x, source_2_y] = source_2_value
    n = 0
    while True:
        #old_data = data.copy()
        #data[1:-1,1:-1] += 0.25*(data[0:-2,1:-1] + data[2:,1:-1] + data[1:-1,0:-2] + data[1:-1,2:] - 4*data[1:-1,1:-1])    
        #change = np.max(np.abs(data - old_data))
        #data[source_1_x, source_1_y] = source_1_value
        #data[source_2_x, source_2_y] = source_2_value
        change = 0
        for i in range(1, data.shape[0]-1):
            for j in range(1, data.shape[1]-1):
                if not ((i==source_1_x and j==source_1_y) or (i==source_2_x and j==source_2_y)):
                    delta = 0.25*(data[i-1,j] + data[i+1,j] + data[i,j-1] + data[i,j+1] - 4*data[i,j])
                    data[i,j] += ovr*delta
                    change = max(abs(change), delta)
        n += 1
        plot_1.set_data('T', data)
        if (change < tolerance) or stop.value:
            break
    # reset the stop button in case it was pushed
    stop.value = False
    messages.write('Number of iterations: %d.\n' % n)
    messages.write('Done.\n')

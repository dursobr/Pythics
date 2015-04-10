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
import random
import numpy as np

from pythics.lib import GrowableArray

#import pdb


#
# basic functionality: initialize, clear, run
#

def initialize(shell, **kwargs):
    shell.interact(kwargs.copy())
    clear(**kwargs)


def clear(seed, messages, plot, **kwargs):
    global x, y, t
    t = 0
    x = 0.0
    y = 0.0
    messages.clear()
    plot.clear()
    plot.set_plot_properties(
        title='Random Walk',
        x_label='x position',
        y_label='y position',
        aspect_ratio='equal')
    plot.new_curve('random_walk', memory='growable', length=10000, animated=True,
                  line_color='red', line_width=0.5)
    random.seed(seed.value)


def run(prob_N_update, messages, plot, stop, **kwargs):
    global x, y, t
    N_update = prob_N_update.value
    messages.write('Starting simulation...\n')
    data = GrowableArray(cols=2, length=1000)
    while True:
        t += 1
        x += random.uniform(-1.0, 1.0)
        y += random.uniform(-1.0, 1.0)
        data.append((x,y))
        if (t % N_update) == 0:
            plot.append_data('random_walk', data[:])
            data.clear()
            if stop.value: break   
    stop.value = False
    messages.write('Stopped simulation, t = %d.\n' % t)

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


#
# basic functionality: initialize, clear, run
#
def initialize(shell, **kwargs):
    shell.interact(kwargs.copy())
    clear(**kwargs)


def clear(messages, plot, **kwargs):
    plot.clear()
    messages.clear()
    plot.set_plot_properties(
        title='Radioactive Decay',
        x_label='t',
        y_label='N',
        x_scale='linear',
        y_scale='log',
        aspect_ratio='auto')
    plot.new_curve('N', memory='growable', length=10000, animated=True,
                  line_style='', marker_style='x')


def run(decay_probability, N_initial, seed, messages, plot, stop, **kwargs):
    N_remaining = N_initial.value
    dp = decay_probability.value
    messages.write('Starting simulation...\n')
    random.seed(seed.value)
    t = 0
    while N_remaining > 1:
        t += 1
        for atom in np.arange(1, N_remaining + 1 ):          # loop over atoms
            decay = random.random()   
            if (decay < dp):
                N_remaining -= 1                                     # a decay
        plot.append_data('N', (t, N_remaining))
        if stop.value: break
    stop.value = False
    messages.write('Stopped simulation, t = %d.\n' % t)

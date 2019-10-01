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

import math
import numpy as np


def initialize_shell(shell, **kwargs):
    shell.interact(kwargs.copy())
    clear(**kwargs)

def clear(plot_1, plot_2, messages, **kwargs):
    plot_1.clear()
    plot_2.clear()
    messages.clear()
    plot_1.set_plot_properties(
        title='Spins',
        x_label='spin #',
        y_label='Direction',
        x_scale='linear',
        y_scale='linear',
        y_limits=(-1.2, 1.2),
        aspect_ratio='auto')
    plot_2.set_plot_properties(
        title='Magnetization',
        x_label='T',
        y_label='M',
        x_scale='linear',
        y_scale='linear',
        y_limits=(-0.1, 1.1),
        aspect_ratio='auto')
    plot_1.new_curve('S', animated=True, line_style='', marker_style='+',
                     marker_width=7)
    plot_2.new_curve('M', memory='growable', animated=True, line_style='', 
                     marker_style='+', marker_width=3)


#------------------------------------------------------------------------------
#  Edit the functions below to accomplish the desired task. Please begin each 
#  run function by writing the question number to the ouput messages box.
#
#  You may need to write additional functions to complete the assignment, and
#  all code you write should be included below.
#------------------------------------------------------------------------------

def Metropolis_sweep(ns, s, T, plot):
    L = s.shape[0]
    for m in range(L):
        n = np.random.randint(0, L)
        dE = 2*s[n]*(s[n-1] + s[(n+1)%L])
        if (dE/T < 0) or (math.exp(-dE/T) > np.random.rand()):
            s[n] *= -1
            plot.set_data('S', np.column_stack([ns, s]))


def metropolis_run(metropolis_L, metropolis_N, metropolis_N_thermalize, metropolis_T,
        stop, messages, plot_1, plot_2, **kwargs):
    L = metropolis_L.value
    N = metropolis_N.value
    N_thermalize = metropolis_N_thermalize.value
    T = metropolis_T.value
    messages.write('\n=== METROPOLIS =========================\n')
    # allocate data arrays   
    spins = np.zeros(L, dtype='int8')
    ns = list(range(L))
    spins[:] = 2*np.random.randint(0, 2, L) - 1
    plot_1.set_data('S', np.column_stack([ns, spins]), rescale=True)
    # the calculation
    M = 0
    for n in range(N):
        Metropolis_sweep(ns, spins, T, plot_1)
        if n >= N_thermalize:
            M += np.sum(spins)
        if stop.value:
            break
    M = float(M)/(L*(N - N_thermalize))
    # reset the stop button in case it was pushed
    stop.value = False
    messages.write('Average M value: %g\n' % M)
    messages.write('Done.\n')


def magnetization_run(magnetization_L, magnetization_N, magnetization_N_thermalize,
        magnetization_T_0, magnetization_T_F, magnetization_N_T,
        stop, messages, plot_1, plot_2, **kwargs):
    plot_1.set_plot_properties(x_title='T')
    L = magnetization_L.value
    N = magnetization_N.value
    N_thermalize = magnetization_N_thermalize.value
    T_0 = magnetization_T_0.value
    T_F = magnetization_T_F.value
    N_T = magnetization_N_T.value
    messages.write('\n=== MAGNETIZATION =========================\n')
    # allocate data arrays   
    spins = np.zeros(L, dtype='int8')
    ns = list(range(L))
    plot_1.set_data('S', np.column_stack([ns, spins]), rescale=True)
    for T in np.linspace(T_0, T_F, N_T):
        spins[:] = 2*np.random.randint(0, 2, L) - 1
        # the calculation
        M = 0
        for n in range(N):
            Metropolis_sweep(ns, spins, T, plot_1)
            if n >= N_thermalize:
                M += np.sum(spins)
            if stop.value:
                break
        if stop.value:
            break
        M = float(M)/(L*(N - N_thermalize))
        plot_2.append_data('M', (T, abs(M)))
    # reset the stop button in case it was pushed
    stop.value = False
    messages.write('Average M value: %g\n' % M)
    messages.write('Done.\n')


def sa_run(sa_L, sa_T_0, sa_T_F, sa_N_T, 
        stop, messages, plot_1, plot_2, **kwargs):
    L = sa_L.value
    T_0 = sa_T_0.value
    T_F = sa_T_F.value
    N_T = sa_N_T.value
    messages.write('\n=== SIMULATED ANNEALING ========================\n')
    plot_2.set_plot_properties(x_scale='log',  y_limits=(-1.1, 1.1))
    # allocate data arrays   
    spins = np.zeros(L, dtype='int8')
    spins[:] = 2*np.random.randint(0, 2, L) - 1
    ns = list(range(L))
    plot_1.set_data('S', np.column_stack([ns, spins]), rescale=True)
    for T in np.logspace(np.log10(T_0), np.log10(T_F), N_T):
        # the calculation
        Metropolis_sweep(ns, spins, T, plot_1)
        M = float(np.sum(spins))/L
        plot_2.append_data('M', (T, M))
        if stop.value: break
    # reset the stop button in case it was pushed
    stop.value = False
    messages.write('Done.\n')
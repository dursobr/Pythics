#
#  Physics 1321: Computational Methods in Physics
#  University of Pittsburgh
#  by Brian R. D'Urso
#

#
# load libraries
#
import math
import random
import numpy as np


#
# basic functionality: initialize, start, stop, clear
#
def initialize(shell, **kwargs):
    shell.interact(kwargs.copy())
    clear(**kwargs)

def clear(messages, plot, **kwargs):
    plot.clear()
    messages.clear()
    plot.set_plot_properties(
        title='Integration Error',
        x_label='N',
        y_label='error',
        x_scale='log',
        y_scale='log',
        aspect_ratio='auto')
    plot.new_curve('trapezoid rule', memory='growable', length=100, animated=True, 
                   line_style='', marker_style='+', marker_edge_color='blue')
    plot.new_curve('Simpsons rule', memory='growable', length=100, animated=True, 
                   line_style='', marker_style='+', marker_edge_color='green')
    plot.new_curve('Monte Carlo', memory='growable', length=100, animated=True, 
                   line_style='', marker_style='+', marker_edge_color='red')


#
# run: the simulation
#
def f(xs):
    return np.exp(-xs)


def run(N_min, N_max, N_multiplier, algorithm, stop, messages, plot, **kwargs):
    random.seed()
    # put simulation stuff here
    a = algorithm.value
    x_min = 0.0
    x_max = 1.0
    answer = 1.0 - math.exp(-1)
    x_span = x_max - x_min
    N_steps = N_min.value
    while N_steps < N_max.value:
        if a == 'trapezoid rule':
            messages.write('Integrating by trapezoid rule...\n')
            dx = x_span/(N_steps - 1)
            xs = np.linspace(x_min, x_max, N_steps)
            ws = np.ones(N_steps)
            ws[0] = 0.5
            ws[-1] = 0.5
            ys = f(xs)*ws
            integral = dx*ys.sum()
            error = abs(integral-answer)
            messages.write('integral = %g, error = %g.\n' % (integral, error))
            if error != 0.0:
                plot.append_data(a, (N_steps, error))
        elif a == 'Simpsons rule':
            messages.write('Integrating by Simpsons rule (odd n only)...\n')
            # make sure N_steps is odd for Simpson's rule
            N_steps_Simpsons = 2*(N_steps / 2) + 1
            dx = x_span/(N_steps_Simpsons - 1)
            xs = np.linspace(x_min, x_max, N_steps_Simpsons)
            ws = np.tile(np.array([2, 4]), (N_steps_Simpsons-1)/2)
            ws[0] = 1
            ws = np.append(ws, 1)
            ys = f(xs)*ws
            integral = dx*ys.sum()/3.0
            error = abs(integral-answer)
            messages.write('integral = %g, error = %g.\n' % (integral, error))
            if error != 0.0:
                plot.append_data(a, (N_steps_Simpsons, error))
        elif a == 'Monte Carlo':
            messages.write('Integrating by Monte Carlo...\n')
            xs = np.random.random(N_steps)*x_span + x_min
            ys = f(xs)
            y_sum = ys.sum()
            integral = x_span*y_sum/N_steps
            error = abs(integral-answer)
            messages.write('integral = %g, error = %g.\n' % (integral, error))
            if error != 0.0:
                plot.append_data(a, (N_steps, error))
        else:
            messages.write('Integration method not recognized.\n')
        N_steps = int(round(N_steps * N_multiplier.value + 1))
        if stop.value: break
    stop.value = False
    messages.write('Done.\n')

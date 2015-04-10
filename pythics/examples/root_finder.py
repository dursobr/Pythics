#
#  Physics 1321: Computational Methods in Physics
#  University of Pittsburgh
#  by Brian R. D'Urso
#

#
# load libraries
#
import math
import numpy as np


def initialize(shell, **kwargs):
    shell.interact(kwargs.copy())
    clear(**kwargs)


def clear(x1, x2, messages, plot, **kwargs):
    global x_1, x_2, x_plot_1, x_plot_2
    x_1 = x1.value
    x_2 = x2.value
    x_plot_1 = x_1
    x_plot_2 = x_2
    plot.clear()
    messages.clear()
    plot.set_plot_properties(
        title='Root Finding',
        x_label='x',
        y_label='f(x)',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')
    plot.new_curve('f', memory='array', animated=True, 
                   line_style='-', line_color='blue')
    plot.new_curve('search', memory='growable', length=100, animated=True, 
                   line_style='-', line_color='red', marker_style='+')


#
# run: the simulation
#
def run(function, algorithm, N, N_plot_steps, messages, plot, **kwargs):
    global x_1, x_2, x_plot_1, x_plot_2
    # put simulation stuff here
    a = algorithm.value
    f_string = function.value
    N_steps = N.value
    N_plot = N_plot_steps.value
    def f(x):
        return eval(f_string)
    # first just plot the function
    xs = np.linspace(x_plot_1, x_plot_2, N_plot)
    ys = np.zeros(N_plot)
    for i in range(N_plot):
        ys[i] = f(xs[i])
    plot.set_data('f', np.column_stack([xs, ys]))
    # now find the root
    if a == 'bisection':
        messages.write('Root finding by bisection...\n')
        for i in range(N_steps):
            x_1, x_2 = bisection(f, x_1, x_2, plot, messages)
    elif a == 'secant':
        messages.write('Root finding by secant method...\n')
        for i in range(N_steps):
            x_1, x_2 = secant(f, x_1, x_2, plot, messages)
    messages.write('Done.\n')


def bisection(f, xm, xp, plot, messages):
    x = (xp + xm)/2.0
    y= f(x)
    if y*f(xp) > 0:
        xp = x
    else:
        xm = x
    messages.write('bisection in  [%g, %g], error = %g\n' % (xm, xp, y))
    plot.append_data('search', (x, y))
    return xm, xp


def secant(f, x1, x2, plot, messages):
    # the following is inefficient, since we already new y2 
    y1 = f(x1)
    y2 = f(x2)
    messages.write('secant: x = %g, error = %g\n' % (x2, y2))
    plot.append_data('search', (x2, y2))
    x3 = x2 - y2*(x2-x1)/(y2-y1)
    x1 = x2
    x2 = x3
    return x1, x2

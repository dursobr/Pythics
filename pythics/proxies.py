# -*- coding: utf-8 -*-
#
# Copyright 2008 - 2019 Brian R. D'Urso
#
# This file is part of Python Instrument Control System, also known as Pythics.
#
# Pythics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pythics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pythics.  If not, see <http://www.gnu.org/licenses/>.
#


#
# load libraries
#
import code, sys, threading, time
import multiprocessing

import pythics.libproxy

try:
    import PIL.Image
    PIL_loaded = True
except ImportError:
    logger = multiprocessing.get_logger()
    logger.warning("'PIL' is not available.")
    PIL_loaded = False


#
# Functions to convert between
# Python Imaging Library (pil) and raw rgb formats
#
def pil_to_rgb(pil_image):
    if (pil_image.mode != 'RGBA'):
        pil_image = pil_image.convert('RGBA')
    image_data = pil_image.tobytes('raw', 'BGRA')
    return image_data, pil_image.size


def rgb_to_pil(image_data, size):
    pil_image = PIL.Image.new('RGBA', size)
    pil_image.frombytes(image_data)
    return pil_image


#
# Helper classes for ShellProxy
#
class stdoutProxy():
    def __init__(self, write_func):
        self.write_func = write_func

    def write(self, text):
        stripped_text = text.rstrip('\n')
        self.write_func(stripped_text)


class ConsoleBackend(code.InteractiveConsole):
    def __init__(self, write_func, *args, **kwargs):
        self.stdout = sys.stdout
        self.stdout_proxy = stdoutProxy(write_func)
        code.InteractiveConsole.__init__(self, *args, **kwargs)
        return

    def get_output(self):
        sys.stdout = self.stdout_proxy

    def return_output(self):
        sys.stdout = self.stdout

    def push(self, data):
        self.get_output()
        r = code.InteractiveConsole.push(self, data)
        self.return_output()
        return r

    def write(self, data):
        self.stdout_proxy.write(data)


#
# Modified ImageProxy which uses shared memory
#
class ImageProxy(pythics.libproxy.PartialAutoProxy):
    def __init__(self, *args, **kwargs):
        local_attrs = ['display']
        pythics.libproxy.PartialAutoProxy.__init__(self, local_attrs, *args, **kwargs)

#    def _get_image(self):
#        r = self._call_method('call_Proxy_method', self._key, '_get_image')
#        return rgb_to_pil(r[0], r[1])
#
#    def _set_image(self, pil):
#        args = pil_to_rgb(pil)
#        self._call_method_no_return('call_Proxy_method_no_return', self._key, '_set_image', *args)
#        
#    image = property(_get_image, _set_image, doc="""None""")

    def display(self, mode, size, data):
        """Display an image in the control.
        
        Arguments:
        
          *mode*: [ 'L' | 'RGB' | 'RGBA' ]
            Image mode 'L' = 8-bit greyscale
                       'RGB' = 3x8-bit pixels, color
                       'RGBA' =  4x8-bit pixels, color with transparency
        
          *size*: tuple
            Size of the image (width, height)
          
          *data*: bytearray
            Image as raw data, with no padding anywhere.
        """
        self._call_method_no_return('call_Proxy_method_no_return', self._key, '_display', mode, size, data)


class ImageWithSharedProxy(pythics.libproxy.PartialAutoProxy):
    def __init__(self, shared_memory, *args, **kwargs):
        local_attrs = ['display']
        self._shared = shared_memory
        pythics.libproxy.PartialAutoProxy.__init__(self, local_attrs, *args, **kwargs)

#    def _get_image(self):
#        w, h = self._call_method('call_Proxy_method', self._key, '_get_image_with_shared')
#        return rgb_to_pil(self._shared.raw[0:(4*w*h)], (w, h))
#
#    def _set_image(self, pil):
#        if (pil.mode != 'RGBA'):
#            pil = pil.convert('RGBA')
#        self._shared.raw = pil.tobytes('raw', 'BGRA')
#        self._call_method_no_return('call_Proxy_method_no_return', self._key, '_set_image_with_shared', pil.size)
#
#    image = property(_get_image, _set_image)

    def display(self, mode, size, data):
        self._shared.raw = data
        self._call_method_no_return('call_Proxy_method_no_return', self._key, '_display_shared', mode, size)


#
# Modified ShellProxy which puts the console backend in the action process
#
class ShellProxy(pythics.libproxy.PartialAutoProxy):
    def __init__(self, queue, *args, **kwargs):
        local_attrs = ['interact', 'push', 'resetbuffer']
        pythics.libproxy.PartialAutoProxy.__init__(self, local_attrs, *args, **kwargs)
        self._queue = queue

    def _start(self, process):
        pythics.libproxy.PartialAutoProxy._start(self, process)
        self._semaphore = threading.Semaphore(1)
        self._thread = threading.Thread(target=self._thread_loop)

    def _stop(self):
        self._queue.put(None)

    def _thread_loop(self):
        while True:
            new_command = self._queue.get()
            if new_command is not None:
                self.push(new_command)
            else:
                break

    def interact(self, local_dict, banner=None):
        self._console = ConsoleBackend(self.write, local_dict)
        if banner != None:
            self.message(banner)
        elif banner != '':
            self.message('Pythics on Python ' + sys.version)
        else:
            self.write_new_prompt()
        self._thread.start()

    def push(self, line):
        self._semaphore.acquire()
        if self._console.push(line):
            self.write_continue_prompt()
        else:
            self.write_new_prompt()
        self._semaphore.release()

    def resetbuffer(self):
        self._semaphore.acquire()
        self._console.resetbuffer()
        self._semaphore.release()


#
# SubWindowProxy is just a modified dictionary
#
class SubWindowProxy(dict):
    def _start(self, process):
        for proxy in self.values():
            if hasattr(proxy, '_start'):
                proxy._start(process)

    def _stop(self):
        for proxy in self.values():
            if hasattr(proxy, '_stop'):
                proxy._stop()



#
# Modified TimerProxy which contains the actual timer functionality
#
class TimerProxy(object):
    def __init__(self, action):
        self.delayed = False
        self._running = False
        self._set_action(action)

    def _start(self, process):
        # initialization delayed until proxy is moved to action process so
        #   threading objects are created in the right process
        self._process = process
        self._parent_to_child_call_queue = self._process.parent_to_child_call_queue
        self._event = threading.Event()
        self._retrigger_event = threading.Event()

    def start(self, interval=1.0, action=None, call_at_zero=True,
              require_retrigger=False, retrigger_timeout=None):
        if not self._running:
            if action != None:
                self._set_action(action)
            self.delayed = False
            self._event.clear()
            self._retrigger_event.clear()
            self._running = True
            self._interval = interval
            self._call_at_zero = call_at_zero
            self._require_retrigger = require_retrigger
            if require_retrigger:
                self._thread = threading.Thread(target=self._thread_loop_with_retrigger)
                self._retrigger_timeout = retrigger_timeout
            else:
                self._thread = threading.Thread(target=self._thread_loop)
            self._thread.start()
        else:
            raise RuntimeWarning('Timer is already running.')

    def stop(self):
        if self._running:
            self._event.set()
            if self._require_retrigger:
                self._retrigger_event.set()
            self._thread.join()
            self._running = False
        else:
            raise RuntimeWarning('Timer is not running.')

    # used to shutdown the thread if timer is running when process is closed
    def _stop(self):
        if self._running:
            self._event.set()
            if self._require_retrigger:
                self._retrigger_event.set()
            self._thread.join()
            self._running = False

    def _get_action(self):
        return self._action

    # not directly accessible, even through a property, to avoid conflicts
    def _set_action(self, action):
        self._action = action
        action_module_name, action_function_name = action.split('.')
        self._queue_action_entry = (action_module_name,
                                    action_function_name)

    action = property(_get_action)

    def _get_interval(self):
        return self._interval

    interval = property(_get_interval)

    def _get_running(self):
        return self._running

    running = property(_get_running)

    def _thread_loop(self):
        if self._call_at_zero:
            # optionally call action once at the start
            self._trigger_action()
        while True:
            self._event.wait(self._interval)
            if self._event.is_set():
                self._event.clear()
                break
            # run timer action
            self._trigger_action()

    def retrigger(self):
        self._retrigger_event.set()

    def _thread_loop_with_retrigger(self):
        if self._call_at_zero:
            # optionally call action once at the start
            self._trigger_action()
        else:
            self._retrigger_event.set()
        while True:
            self._event.wait(self._interval)
            if self._event.is_set():
                self._event.clear()
                break
            delayed = not self._retrigger_event.is_set()
            self._retrigger_event.wait(self._retrigger_timeout)
            self._retrigger_event.clear()
            self.delayed = delayed
            # run timer action
            self._trigger_action()

    def _trigger_action(self):
        self._parent_to_child_call_queue.put(self._queue_action_entry)


#
# Modified EventButtonProxy which contains the timing functionality
#
class EventButtonProxy(pythics.libproxy.PartialAutoProxy):
    def __init__(self, event, *args, **kwargs):
        local_attrs = ['clear', 'is_set', 'wait_interval', 'wait']
        pythics.libproxy.PartialAutoProxy.__init__(self, local_attrs, *args, **kwargs)
        self._last_time = time.time()
        self._event = event

    def clear(self):
        """Clear the Event."""
        self._event.clear()

    def is_set(self):
        """Check and return whether the Event is set. The Event is set when the 
        button is pressed (when toggle=False) or when the button is toggled to
        unpressed (when toggle=True).
        """
        return self._event.is_set()
        
    def start_interval(self):
        """Start the timer used for the firt call to wait_interval()."""
        self._last_time = time.time()

    def wait_interval(self, t):
        """Wait t seconds since the last call to start_interval() or 
        wait_interval(). This wait can be interrupted by any action that sets 
        the Event.
        """
        # calculate how long we need to wait
        sleep_time = t - (time.time() - self._last_time)
        if sleep_time > 0 :
            result = self._event.wait(sleep_time)
        else:
            result = self._event.is_set()
        self._last_time = time.time()
        return result

    def wait(self, t):
        """Wait t seconds. This wait can be interrupted by any action that sets 
        the Event.
        """
        return self._event.wait(t)


#
# Modified RunButtonProxy which contains the timing functionality
#
class RunButtonProxy(pythics.libproxy.PartialAutoProxy):
    def __init__(self, proxy_id, action, time_interval, *args, **kwargs):
        local_attrs = ['start', 'step', 'stop', 'abort', 'kill', 'action', 'running', 'value', 'delayed']
        pythics.libproxy.PartialAutoProxy.__init__(self, local_attrs, *args, **kwargs)
        self._time_interval = time_interval
        # self._running should only be True when the thread is running
        self._running = False
        self._set_action(action)
        self._step_message = (None, pythics.libproxy.ProxyMessage(proxy_id, 'step'))
        self.delayed = False

    def _start(self, process):
        # initialization delayed until proxy is moved to action process so
        #   threading objects are created in the right process
        pythics.libproxy.PartialAutoProxy._start(self, process)
        self._parent_to_child_call_queue = self._process.parent_to_child_call_queue
        self._abort_event = threading.Event()
        self._stop_event = threading.Event()
        self._yield_event = threading.Event()
        self._interval_semaphore = threading.Semaphore(1)

    # used to shutdown the thread if timer is running when process is closed
    def _stop(self):
        if self._running:
            self._stop_event.set()
            self._yield_event.set()
            self._abort_event.set()
            self._thread.join()

    def _get_action(self):
        return self._action

    def _set_action(self, action):
        if not self._running:
            self._action = action
            action_module_name, action_function_name = action.split('.')
            self._queue_action_entry = (action_module_name,
                                        action_function_name)
        else:
            raise RuntimeWarning('action cannot be set while RunButton is running.')
            
    action = property(_get_action, _set_action, doc=\
        """The function (generator) to run when started. 
        Format: a string of the form of module.function.
        """)
        
    def _get_running(self):
        return self._running

    running = property(_get_running, doc=\
        """This read-only property holds the state of the RunButton thread.

        If *running* is True, the thread is running. If *running* is False, the
        thread is not running.
        """)
    
    def _get_value(self):
        return self._call_method('call_Proxy_method', self._key, '_get_value')

    value = property(_get_value, doc=\
        """This read-only property holds the state of the RunButton.

        If *value* is True, the RunButton is pressed. If *value* is False, the
        RunButton is not pressed.
        """)

    def start(self, update_button_state=True):
        """Request the RunButton to start. Equivlent to pressing the button to start.
        Do not use this function to restart the RunButton from within your run action. 
        Use the resume function instead."""
        if not self._running:
            if update_button_state:
                self._call_method_no_return('call_Proxy_method_no_return', self._key, '_set_value', True)
            # setup action
            called_module_name, called_function_name = self._queue_action_entry
            called_module = self._process.modules[called_module_name]
            f = getattr(called_module, called_function_name)
            self._generator = f(**self._process.control_proxies)
            # start thread
            self.delayed = False
            self._interval = 0.0
            self._abort_event.clear()
            self._stop_event.clear()
            self._yield_event.clear()
            if self._time_interval:
                self._thread = threading.Thread(target=self._thread_loop_time_interval)
            else:
                self._thread = threading.Thread(target=self._thread_loop)
            self._running = True
            self._thread.start()
        else:
            raise RuntimeWarning('RunButton is already running.')

    def resume(self, update_button_state=True):
        """Request the RunButton to resume running after stop has been pressed 
        or abort has been called but the run action has not returned. This 
        should be used to cancel a stop from within your run action. It will 
        not cancel a kill request."""
        if self._running:
            if update_button_state:
                self._call_method_no_return('call_Proxy_method_no_return', self._key, '_set_value', True)
            # reset _abort_event to make yield events work again
            self._abort_event.clear()
        else:
            raise RuntimeWarning('RunButton is not running and cannot be resumed.')

    def _thread_loop(self):
        # run action
        self._parent_to_child_call_queue.put(self._step_message)
        while True:
            self._yield_event.wait()
            self._yield_event.clear()
            # check for stop condition
            if self._stop_event.is_set():
                break
            self._interval_semaphore.acquire()
            interval = self._interval
            self._interval_semaphore.release()
            self._abort_event.wait(interval)
            # check for stop again in case of a kill
            if self._stop_event.is_set():
                break
            # run action
            self._parent_to_child_call_queue.put(self._step_message)

    def _thread_loop_time_interval(self):
        last_time = time.time()
        # run action
        self._parent_to_child_call_queue.put(self._step_message)
        while True:
            self._yield_event.wait()
            self._yield_event.clear()
            if self._stop_event.is_set():
                break
            self._interval_semaphore.acquire()
            interval = self._interval
            self._interval_semaphore.release()
            sleep_time = interval - (time.time() - last_time)
            if sleep_time > 0 :
                self.delayed = False
                self._abort_event.wait(sleep_time)
                # check for stop again in case of a kill
                if self._stop_event.is_set():
                    break
            else:
                self.delayed = True
            last_time = time.time()
            # run action
            self._parent_to_child_call_queue.put(self._step_message)

    def step(self):
        """Take a step. Normally for internal use only."""
        try:
            # get the value returned by yield
            # default to 0.0 if no return value is given
            interval = next(self._generator) or 0.0
            self._interval_semaphore.acquire()
            self._interval = interval
            self._interval_semaphore.release()
            # tell the loop we are ready for another step
            self._yield_event.set()
        except StopIteration:
            # the generator returned (not yielded) on its own, so stop
            self.kill()
        except:
            # the generator had some other problem, so stop but propagate exception
            self.kill()
            raise

    def stop(self):
        """Request the RunButton to stop. Equivlent to pressing the button to stop."""
        if self._running:
            self._call_method_no_return('call_Proxy_method_no_return', self._key, '_set_value', False)
            self.abort()
        else:
            raise RuntimeWarning('RunButton is not running.')

    def abort(self):
        """Abort the current wait in the RunButton. This may not stop your function."""
        # don't check self._running because this call can get out of order with kill
        self._abort_event.set()

    def kill(self):
        """Try to force the RunButton to stop. This may leave your function in a poorly defined state."""
        if self._running:
            self._call_method_no_return('call_Proxy_method_no_return', self._key, '_set_value', False)
            self._stop_event.set()
            self._yield_event.set()
            self._abort_event.set()
            self._thread.join()
            self._running = False
        else:
            raise RuntimeWarning('RunButton is not running.')

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
import multiprocessing
import pickle

import numpy as np
import collections

from pythics.settings import _TRY_PYSIDE
try:
    if not _TRY_PYSIDE:
        raise ImportError()
    import PySide2.QtCore as _QtCore
    import PySide2.QtGui as _QtGui
    import PySide2.QtWidgets as _QtWidgets
    import PySide2.QtPrintSupport as _QtPrintSupport
    QtCore = _QtCore
    QtGui = _QtGui
    QtWidgets = _QtWidgets
    QtPrintSupport = _QtPrintSupport
    Signal = QtCore.Signal
    Slot = QtCore.Slot
    Property = QtCore.Property
    USES_PYSIDE = True
except ImportError:
    import PyQt5.QtCore as _QtCore
    import PyQt5.QtGui as _QtGui
    import PyQt5.QtWidgets as _QtWidgets
    import PyQt5.QtPrintSupport as _QtPrintSupport
    QtCore = _QtCore
    QtGui = _QtGui
    QtWidgets = _QtWidgets
    QtPrintSupport = _QtPrintSupport
    Signal = QtCore.pyqtSignal
    Slot = QtCore.pyqtSlot
    Property = QtCore.pyqtProperty
    USES_PYSIDE = False

import pythics.child
import pythics.libproxy
 

#
# Parent is the main object which manages everything in Pythics.
#   You should usually create only one instance
#
class Parent(QtCore.QObject):
    def __init__(self, manager):
        QtCore.QObject.__init__(self)
        self.multiprocess_manager = manager
        self.child_to_parent_call_queue = self.multiprocess_manager.Queue()
        self.global_namespaces = dict()
        self.global_actions = dict()
        self.last_child_process_index = 0
        self.child_processes = dict()
        self.logger = multiprocessing.get_logger()

    def start(self):
        # thread to relay command requests from child processes to GUI
        self.watcher_thread = QtCore.QThread()
        self.watcher = QueueWatcher(self, self.child_to_parent_call_queue, self.logger)
        self.watcher.moveToThread(self.watcher_thread)
        self.watcher.call_requested.connect(self.exec_child_to_parent_call_request,
                                            type=QtCore.Qt.QueuedConnection)
        self.watcher_thread.started.connect(self.watcher.watch_queue)
        self.watcher_thread.start()

    # USED FOR ALTERNATIVE SIGNALLING METHOD USING POST_EVENT
    #def customEvent(self, command_event):
    #    self.exec_child_to_parent_call_request(command_event.command)

    def exec_child_to_parent_call_request(self, command):
        # executes a command in a control requested by a child process
        # protect from exceptions to avoid interrupting program
        try:
            process_id, function_name, args, kwargs = command
            #self.logger.debug('Executing %s.' % str((process_id, function_name, args, kwargs)))
            self.child_processes[process_id].exec_child_to_parent_call_request(function_name, args, kwargs)
        except:
            self.logger.exception('Error in Parent.execute_child_to_parent_call_request while executing call request from child process in parent process.')

    def new_child_process(self, path, name, anonymous_controls, controls):
        new_index = self.last_child_process_index + 1
        new_id = str(new_index)
        self.last_child_process_index = new_index
        name = name + '_' + new_id
        new_process = ChildInterface(self,
                                     self.child_to_parent_call_queue,
                                     self.multiprocess_manager,
                                     new_id,
                                     path, name, anonymous_controls, controls)
        self.child_processes[new_id] = new_process
        return new_process

    def get_global_namespace(self, name):
        if name in self.global_namespaces:
            g = self.global_namespaces[name]
        else:
            g = self.multiprocess_manager.Namespace()
            self.global_namespaces[name] = g
        return g

    def trigger_global_action(self, trigger_id):
        if trigger_id in self.global_actions:
            actions = self.global_actions[trigger_id]
            for a in actions:
                process_id, proxy_key = a
                if process_id in self.child_processes:
                    self.child_processes[process_id].exec_trigger_request(proxy_key)
                else:
                    # that process is not around anymore, so remove the action
                    actions.remove(a)
        else:
            self.logger.warning("No action found for global trigger '%s'." % trigger_id)

    def new_global_action(self, process_id, trigger_id, proxy_key):
        if trigger_id in self.global_actions:
            self.global_actions[trigger_id].append((process_id, proxy_key))
        else:
            self.global_actions[trigger_id] = [(process_id, proxy_key)]

    def stop_child_process(self, process):
        process.stop()
        self.child_processes.pop(process.process_id)

    def stop(self):
        # stop the ChildProcesses
        for p in self.child_processes.values():
            p.stop()
        # stop the QueueWatcher
        self.child_to_parent_call_queue.put((None, None, None, None))
        self.logger.debug('Signaled QueueWatcher to stop.')
        self.watcher_thread.quit()
        # wait 2 seconds for the thread to die
        success = self.watcher_thread.wait(2000)
        self.logger.debug('QueueWatcher stopped? ' + str(success))


#
# object which gets moved to the parent process queue watching thread
#
class QueueWatcher(QtCore.QObject):
    def __init__(self, parent, queue_to_watch, logger, *args):
        super(QueueWatcher, self).__init__(*args)
        self.parent = parent
        self.watched_queue = queue_to_watch
        self.logger = logger

    # define a Qt signal 'call_requested' that takes a tuple argument
    call_requested = Signal(tuple, name='call_requested')

    def watch_queue(self):
        # executes in the parent process, queue watcher thread
        stop = False
        while stop == False:
            try:
                command = self.watched_queue.get()
                #self.logger.debug("Parent watch_queue loop received '%s'" % str(command))
                if command[0] is not None:
                    self.call_requested.emit(command)
                    # USED FOR ALTERNATIVE SIGNALLING METHOD USING POST_EVENT
                    #QtCore.QCoreApplication.postEvent(self.parent,
                    #                                  CommandEvent(command))
                else:
                    self.logger.debug('QueueWatcher.watch_queue() has detected a stop request.')
                    stop = True
            except:
                self.logger.exception('Error in QueueWatcher.watch_queue().')
        self.logger.debug('QueueWatcher.watch_queue() is exiting.')


# USED FOR ALTERNATIVE SIGNALLING METHOD USING POST_EVENT
#class CommandEvent(QtCore.QEvent):
#    def __init__(self, command, *args, **kwargs):
#        self.command = command
#        QtCore.QEvent.__init__(self, QtCore.QEvent.User)


#
# Interface for child processes from the parent process
#   Create one instance for each child process.
#
class ChildInterface(object):
    def __init__(self, parent, child_to_parent_call_queue, manager, process_id,
                 path, name, anonymous_controls, controls):
        self.parent = parent
        self.logger = multiprocessing.get_logger()
        self.child_to_parent_call_queue = child_to_parent_call_queue
        self.manager = manager
        self.process_id = process_id
        self.path = path
        self.name = name
        self.default_parameter_filename = 'defaults.txt'
        # dictionary of controls (widgets)
        self.controls = controls
        # list of controls without ids
        self.anonymous_controls = anonymous_controls
        # queues for communication between parent and child
        self.parent_to_child_call_queue = manager.Queue()
        self.child_to_parent_call_return_queue = manager.Queue()
        # This semaphore restricts the number of GUI requests from each
        #  child process to a certain number at any time.
        #  The number of requests available to each process can be set here.
        #  The minimum preferable value is 2 in order to be sure the GUI
        #  process remains busy. Setting it to 1 would effectively give
        #  completely synchronous execution. Higher values would potentially
        #  buffer more requests.
        self.child_to_parent_call_queue_semaphore = manager.Semaphore(2)
        self.child_process = None
        # objects which have proxies
        self.objects = dict()
        self.fully_picklable_types = [int, float, bool, str, type(None), np.ndarray]
        self.fully_picklable_types.extend(list(np.typeDict.values()))
        self.control_proxies = dict()
        self.module_names = list()
        self.initialization_commands = list()
        self.termination_commands = list()
        # loop through controls to create proxies, etc.
        for k, v in controls.items():
            # _register() is an opportunity for controls to add to:
            #   module_names, initialization_commands, termination_commands,
            #   or to add global variables
            proxy_key = self.new_ProxyKey(v)
            if hasattr(v, '_register'):
                try:
                    v._register(self, k, proxy_key)
                except:
                    self.logger.exception("Exception occured while registering control '%s'." % k)
            # update control_proxies
            if hasattr(v, '_proxy'):
                # use a custom proxy
                self.control_proxies[k] = v._proxy
            else:
                # use a standard AutoProxy
                self.control_proxies[k] = pythics.libproxy.AutoProxy(proxy_key, enable_cache=True)
        for v in anonymous_controls:
            if hasattr(v, '_register'):
                v._register(self, None, None)

    def start(self):
        child = pythics.child.Child(self.process_id,
                      self.child_to_parent_call_queue,
                      self.child_to_parent_call_return_queue,
                      self.child_to_parent_call_queue_semaphore,
                      self.parent_to_child_call_queue,
                      self.path,
                      self.module_names,
                      self.control_proxies)
        self.child_process = multiprocessing.Process(name=self.name,
                                                     target=child.process_loop)
        self.child_process.start()
        # call initialization functions
        for item in self.initialization_commands:
            self.exec_parent_to_child_call_request(item)

    def new_global_namespace(self, element_id):
        namespace = self.parent.get_global_namespace(element_id)
        return namespace

    def new_global_action(self, element_id, proxy_key):
        self.parent.new_global_action(self.process_id, element_id, proxy_key)

    def trigger_global_action(self, action_id):
        self.parent.trigger_global_action(action_id)

    def append_initialization_command(self, command):
        self.initialization_commands.append(command)

    def append_termination_command(self, command):
        self.termination_commands.append(command)

    def append_module_name(self, module_name):
        if not module_name in self.module_names:
            self.module_names.append(module_name)

    def exec_child_to_parent_call_request(self, function_name, args, kwargs):
        # executes a command in this (ChildInterface) object
        f = getattr(self, function_name)
        f(*args, **kwargs)

    def exec_parent_to_child_call_request(self, command):
        c = command.split('.')
        self.logger.debug("Put in parent_to_child_call_queue: '%s'." % str((c[0], c[1])))
        self.parent_to_child_call_queue.put((c[0], c[1]))

    def exec_parent_to_proxy_call_request(self, proxy_id, method, *args, **kwargs):
        message = pythics.libproxy.ProxyMessage(proxy_id, method, *args, **kwargs)
        self.logger.debug("Put in parent_to_child_call_queue: '%s'." % str((None, message)))
        self.parent_to_child_call_queue.put((None, message))

    def exec_trigger_request(self, proxy_key):
        self.lookup(proxy_key)._exec_action('triggered')

    def load_parameters(self, filename=None):
        if filename is None:
            filename = self.default_parameter_filename
        try:
            with open(filename, 'rb') as file:
                temp_dict = pickle.load(file)
        except:
            self.logger.error("Problem loading parameter file '%s'. Parameter loading aborted." % filename)
        else:
            for k, v in temp_dict.items():
                try:
                    self.controls[k]._set_parameter(v)
                except KeyError:
                    self.logger.error("id '%s' in parameter file has no corresponding control." % k)
                except:
                    self.logger.exception("Exception while loading parameter from control '%s'" % k)

    def save_parameters(self, filename=None):
        if filename is None:
            filename = self.default_parameter_filename
        with open(filename, 'wb') as file:
            temp_dict = dict()
            for k, v in self.controls.items():
                try:
                    if hasattr(v, 'save') and v.save == True:
                        if hasattr(v, '_get_parameter'):
                            temp_dict[k] = v._get_parameter()
                except:
                    self.logger.exception("Exception while saving parameter from control '%s'" % k)
            pickle.dump(temp_dict, file, 0)

    def redraw(self):
        for k, c in self.controls.items():
            if hasattr(c, '_redraw'):
                c._redraw()

    def stop(self):
        # passing (None, None) triggers the process to stop
        try:
            # call termination functions
            for item in self.termination_commands:
                self.exec_parent_to_child_call_request(item)
            self.logger.info("Stopping process '%s'." % self.name)
            if self.child_process.is_alive():
                self.logger.debug("Passing (None, None) to process '%s'." % self.name)
                self.parent_to_child_call_queue.put((None, None))
                # try to stop the process; give it 5 seconds to stop peacefully
                self.logger.debug("Waiting for join() to process '%s'." % self.name)
                self.child_process.join(5.0)
                if self.child_process.is_alive():
                    self.child_process.terminate()
                    self.logger.error("Action process '%s' was terminated abnormally." % self.name)
                else:
                    self.logger.info("Process '%s' was terminated normally." % self.name)
            else:
                self.logger.error("Action process '%s' was already dead." % self.name)
        except:
                self.logger.exception("Error while trying to stop process '%s'." % self.name)

    #------------------------------------------------
    # methods for proxy handling

    def new_ProxyKey(self, original_object, cache=False):
        new_key = 'AutoProxy_key_' + str(type(original_object)) + '_' + str(id(original_object))
        new_proxy = pythics.libproxy.ProxyKey(new_key, cache)
        if new_key in self.objects:
            self.objects[new_key] = (self.objects[new_key][0] + 1, original_object)
        else:
            self.objects[new_key] = (1, original_object)
        return new_proxy

    def lookup(self, proxy_key):
        return self.objects[proxy_key.key][1]

    def objects_to_keys(self, value):
        t = type(value)
        if t in self.fully_picklable_types:
            # a simple picklable type, doesn't need proxy
            return value
        elif t is list:
            # have to check for unpicklable objects in the list
            r = list()
            for v in value:
                r.append(self.objects_to_keys(v))
            return r
        elif t is tuple:
            # have to check for unpicklable objects in the tuple
            r = list()
            for v in value:
                r.append(self.objects_to_keys(v))
            return tuple(r)
        elif t is dict:
            # have to check for unpicklable objects in the dict
            r = dict()
            for k, v in value.items():
                r[k] = self.objects_to_keys(v)
            return r
        else:
            # some other type that has to be accessed by proxy
            #  because it may not be picklable
            if isinstance(value, collections.Callable):
                # request that functions be cached since they usually don't change
                return self.new_ProxyKey(value, cache=True)
            else:
                return self.new_ProxyKey(value, cache=False)

    def keys_to_objects(self, value):
        # create a new object with any AutoProxy keys replaced by
        #  the original objects
        t = type(value)
        if t is pythics.libproxy.ProxyKey:
            # some other type that has to be accessed by proxy
            #  because it may not be picklable
            return self.lookup(value)
        elif t is list:
            # have to check for ProxyKeys in the list
            r = list()
            for v in value:
                r.append(self.keys_to_objects(v))
            return r
        elif t is tuple:
            # have to check for ProxyKeys in the tuple
            r = list()
            for v in value:
                r.append(self.keys_to_objects(v))
            return tuple(r)
        elif t is dict:
            # have to check for ProxyKeys in the dict
            r = dict()
            for k, v in value.items():
                r[k] = self.keys_to_objects(v)
            return r
        elif t is pythics.libproxy.FunctionProxy:
            name = value.name
            return lambda *args, **kwargs: self.exec_parent_to_child_call_request(name)
        else:
            # hopefully just a picklable type
            return value

    #------------------------------------------------
    # methods for use by AutoProxy

    def call_Proxy(self, proxy_key, *args, **kwargs):
        try:
            a = self.keys_to_objects(args)
            kwa = self.keys_to_objects(kwargs)
            r = self.lookup(proxy_key)(*a, **kwa)
            ret = self.objects_to_keys(r)
        except Exception as e:
            cpe = pythics.libproxy.CrossProcessExceptionProxy(str(e))
            self.child_to_parent_call_return_queue.put(cpe)
            # re-raise exception in this process
            raise
        else:
            self.child_to_parent_call_return_queue.put(ret)
        finally:
            self.child_to_parent_call_queue_semaphore.release()

    def get_Proxy_attr(self, proxy_key, name):
        try:
            r = getattr(self.lookup(proxy_key), name)
            ret = self.objects_to_keys(r)
        except Exception as e:
            cpe = pythics.libproxy.CrossProcessExceptionProxy(str(e))
            self.child_to_parent_call_return_queue.put(cpe)
            # re-raise exception in this process
            raise
        else:
            self.child_to_parent_call_return_queue.put(ret)
        finally:
            self.child_to_parent_call_queue_semaphore.release()

    def set_Proxy_attr(self, proxy_key, name, value):
        try:
            v = self.keys_to_objects(value)
            setattr(self.lookup(proxy_key), name, v)
        except Exception:
            logger = multiprocessing.get_logger()
            logger.exception('Exception raised in parent thread that cannot propagate to action process.')
            # re-raise exception in this process
            raise
        finally:
            self.child_to_parent_call_queue_semaphore.release()

    def call_Proxy_method(self, proxy_key, method_name, *args, **kwargs):
        try:
            a = self.keys_to_objects(args)
            kwa = self.keys_to_objects(kwargs)
            r = getattr(self.lookup(proxy_key), method_name)(*a, **kwa)
            ret = self.objects_to_keys(r)
        except Exception as e:
            cpe = pythics.libproxy.CrossProcessExceptionProxy(str(e))
            self.child_to_parent_call_return_queue.put(cpe)
            # re-raise exception in this process
            raise
        else:
            self.child_to_parent_call_return_queue.put(ret)
        finally:
            self.child_to_parent_call_queue_semaphore.release()

    def call_Proxy_method_no_return(self, proxy_key, method_name, *args, **kwargs):
        try:
            a = self.keys_to_objects(args)
            kwa = self.keys_to_objects(kwargs)
            getattr(self.lookup(proxy_key), method_name)(*a, **kwa)
        except Exception:
            logger = multiprocessing.get_logger()
            logger.exception('Exception raised in parent thread that cannot propagate to action process.')
            # re-raise exception in this process
            raise
        finally:
            self.child_to_parent_call_queue_semaphore.release()

    def delete_Proxy(self, proxy_key):
        try:
            k = proxy_key.key
            entry = self.objects[k]
            if entry[0] == 1:
                self.objects.pop(k)
            else:
                self.objects[k] = (entry[0] - 1, entry[1])
        except Exception:
            logger = multiprocessing.get_logger()
            logger.exception('Exception raised in parent thread that cannot propagate to action process.')
            # re-raise exception in this process
            raise
        finally:
            self.child_to_parent_call_queue_semaphore.release()

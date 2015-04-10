# -*- coding: utf-8 -*-
#
# Copyright 2008 - 2014 Brian R. D'Urso
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
import types

import numpy as np
#from PyQt4 import QtCore
from pythics.settings import _TRY_PYSIDE
try:
    if not _TRY_PYSIDE:
        raise ImportError()
    import PySide.QtCore as _QtCore
    import PySide.QtGui as _QtGui
    QtCore = _QtCore
    QtGui = _QtGui
    USES_PYSIDE = True
except ImportError:
    import sip
    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)
    import PyQt4.QtCore as _QtCore
    import PyQt4.QtGui as _QtGui
    QtCore = _QtCore
    QtGui = _QtGui
    USES_PYSIDE = False

import pythics.slave
import pythics.libproxy


if USES_PYSIDE:
	Signal = QtCore.Signal
	Slot = QtCore.Slot
	Property = QtCore.Property
else:
	Signal = QtCore.pyqtSignal
	Slot = QtCore.pyqtSlot
	Property = QtCore.pyqtProperty
 

#
# Master is the main object which manages everything in Pythics.
#   You should usually create only one instance
#
class Master(QtCore.QObject):
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.multiprocess_manager = multiprocessing.Manager()
        self.slave_to_master_call_queue = self.multiprocess_manager.Queue()
        self.global_namespaces = dict()
        self.global_actions = dict()
        self.last_slave_process_index = 0
        self.slave_processes = dict()
        self.logger = multiprocessing.get_logger()

    def start(self):
        # thread to relay command requests from slave processes to GUI
        self.watcher_thread = QtCore.QThread()
        self.watcher = QueueWatcher(self, self.slave_to_master_call_queue, self.logger)
        self.watcher.moveToThread(self.watcher_thread)
        self.watcher.call_requested.connect(self.exec_slave_to_master_call_request,
                                            type=QtCore.Qt.QueuedConnection)
        self.watcher_thread.started.connect(self.watcher.watch_queue)
        self.watcher.finished.connect(self.stop_watcher)
        self.watcher_thread.start()

    def stop_watcher(self):
        self.watcher_thread.quit()
        # wait 2 seconds for the thread to die
        success = self.watcher_thread.wait(2000)
        self.logger.debug('QueueWatcher stopped? ' + str(success))

    # USED FOR ALTERNATIVE SIGNALLING METHOD USING POST_EVENT
    #def customEvent(self, command_event):
    #    self.exec_slave_to_master_call_request(command_event.command)

    def exec_slave_to_master_call_request(self, command):
        # executes a command in a control requested by a slave process
        # protect from exceptions to avoid interrupting program
        try:
            process_id, function_name, args, kwargs = command
            #self.logger.debug('Executing %s.' % str((process_id, function_name, args, kwargs)))
            self.slave_processes[process_id].exec_slave_to_master_call_request(function_name, args, kwargs)
        except:
            self.logger.exception('Error in MasterManager.execute_slave_to_master_call_request while executing call request from slave process in master process.')

    def new_slave_process(self, path, name, anonymous_controls, controls):
        new_index = self.last_slave_process_index + 1
        new_id = str(new_index)
        self.last_slave_process_index = new_index
        name = name + '_' + new_id
        new_process = SlaveInterface(self,
                                     self.slave_to_master_call_queue,
                                     self.multiprocess_manager,
                                     new_id,
                                     path, name, anonymous_controls, controls)
        self.slave_processes[new_id] = new_process
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
                if process_id in self.slave_processes:
                    self.slave_processes[process_id].exec_trigger_request(proxy_key)
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

    def stop_slave_process(self, process):
        process.stop()
        self.slave_processes.pop(process.process_id)

    def stop(self):
        # stop the SlaveProcesses
        for p in self.slave_processes.itervalues():
            p.stop()
        # stop the QueueWatcher
        self.slave_to_master_call_queue.put((None, None, None, None))
        self.logger.debug('Signaled QueueWatcher to stop.')


#
# object which gets moved to the master process queue watching thread
#
class QueueWatcher(QtCore.QObject):
    def __init__(self, master, queue_to_watch, logger, *args):
        super(QueueWatcher, self).__init__(*args)
        self.master = master
        self.watched_queue = queue_to_watch
        self.logger = logger

    # define a Qt signal 'call_requested' that takes a tuple argument
    call_requested = Signal(tuple, name='call_requested')

    # a Qt signal to exit the thread
    finished = Signal(name='finished')

    def watch_queue(self):
        # executes in the master process, queue watcher thread
        stop = False
        while stop == False:
            try:
                command = self.watched_queue.get()
                #self.logger.debug("Master watch_queue loop received '%s'" % str(command))
                if command[0] is not None:
                    self.call_requested.emit(command)
                    # USED FOR ALTERNATIVE SIGNALLING METHOD USING POST_EVENT
                    #QtCore.QCoreApplication.postEvent(self.master,
                    #                                  CommandEvent(command))
                else:
                    self.logger.debug('QueueWatcher.watch_queue() has detected a stop request.')
                    stop = True
            except:
                self.logger.exception('Error in QueueWatcher.watch_queue().')
        self.logger.debug('QueueWatcher.watch_queue() is exiting.')
        self.finished.emit()


# USED FOR ALTERNATIVE SIGNALLING METHOD USING POST_EVENT
#class CommandEvent(QtCore.QEvent):
#    def __init__(self, command, *args, **kwargs):
#        self.command = command
#        QtCore.QEvent.__init__(self, QtCore.QEvent.User)


#
# Interface for slave processes from the master process
#   Create one instance for each slave process.
#
class SlaveInterface(object):
    def __init__(self, master, slave_to_master_call_queue, manager, process_id,
                 path, name, anonymous_controls, controls):
        self.master = master
        self.logger = multiprocessing.get_logger()
        self.slave_to_master_call_queue = slave_to_master_call_queue
        self.manager = manager
        self.process_id = process_id
        self.path = path
        self.name = name
        self.default_parameter_filename = 'defaults.txt'
        # dictionary of controls (widgets)
        self.controls = controls
        # list of controls without ids
        self.anonymous_controls = anonymous_controls
        # queues for communication between master and slave
        self.master_to_slave_call_queue = manager.Queue()
        self.slave_to_master_call_return_queue = manager.Queue()
        # This semaphore restricts the number of GUI requests from each
        #  slave process to a certain number at any time.
        #  The number of requests available to each process can be set here.
        #  The minimum preferable value is 2 in order to be sure the GUI
        #  process remains busy. Setting it to 1 would effectively give
        #  completely synchronous execution. Higher values would potentially
        #  buffer more requests.
        self.slave_to_master_call_queue_semaphore = manager.Semaphore(2)
        self.slave_process = None
        # objects which have proxies
        self.objects = dict()
        self.fully_picklable_types = [int, long, float, bool, str, unicode, types.NoneType, np.ndarray]
        self.fully_picklable_types.extend(np.typeDict.values())
        self.control_proxies = dict()
        self.module_names = list()
        self.initialization_commands = list()
        self.termination_commands = list()
        # loop through controls to create proxies, etc.
        for k, v in controls.iteritems():
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
        slave = pythics.slave.Slave(self.process_id,
                      self.slave_to_master_call_queue,
                      self.slave_to_master_call_return_queue,
                      self.slave_to_master_call_queue_semaphore,
                      self.master_to_slave_call_queue,
                      self.path,
                      self.module_names,
                      self.control_proxies)
        self.slave_process = multiprocessing.Process(name=self.name,
                                                     target=slave.process_loop)
        self.slave_process.start()
        # call initialization functions
        for item in self.initialization_commands:
            self.exec_master_to_slave_call_request(item)

    def new_global_namespace(self, element_id):
        namespace = self.master.get_global_namespace(element_id)
        return namespace

    def new_global_action(self, element_id, proxy_key):
        self.master.new_global_action(self.process_id, element_id, proxy_key)

    def trigger_global_action(self, action_id):
        self.master.trigger_global_action(action_id)

    def append_initialization_command(self, command):
        self.initialization_commands.append(command)

    def append_termination_command(self, command):
        self.termination_commands.append(command)

    def append_module_name(self, module_name):
        if not module_name in self.module_names:
            self.module_names.append(module_name)

    def exec_slave_to_master_call_request(self, function_name, args, kwargs):
        # executes a command in this (SlaveInterface) object
        f = getattr(self, function_name)
        f(*args, **kwargs)

    def exec_master_to_slave_call_request(self, command):
        c = command.split('.')
        self.logger.debug("Put in master_to_slave_call_queue: '%s'." % str((c[0], c[1])))
        self.master_to_slave_call_queue.put((c[0], c[1]))

    def exec_master_to_proxy_call_request(self, proxy_id, method, *args, **kwargs):
        message = pythics.libproxy.ProxyMessage(proxy_id, method, *args, **kwargs)
        self.logger.debug("Put in master_to_slave_call_queue: '%s'." % str((None, message)))
        self.master_to_slave_call_queue.put((None, message))

    def exec_trigger_request(self, proxy_key):
        self.lookup(proxy_key)._exec_action('triggered')

    def load_parameters(self, filename=None):
        if filename is None:
            filename = self.default_parameter_filename
        try:
            with open(filename, 'rU') as file:
                temp_dict = pickle.load(file)
        except:
            self.logger.error("Problem loading parameter file '%s'. Parameter loading aborted." % filename)
        else:
            for k, v in temp_dict.iteritems():
                try:
                    self.controls[k]._set_parameter(v)
                except KeyError:
                    self.logger.error("id '%s' in parameter file has no corresponding control." % k)
                except:
                    self.logger.exception("Exception while loading parameter from control '%s'" % k)

    def save_parameters(self, filename=None):
        if filename is None:
            filename = self.default_parameter_filename
        with open(filename, 'w') as file:
            temp_dict = dict()
            for k, v in self.controls.iteritems():
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
                self.exec_master_to_slave_call_request(item)
            self.logger.info("Stopping process '%s'." % self.name)
            if self.slave_process.is_alive():
                self.master_to_slave_call_queue.put((None, None))
                # try to stop the process; give it 5 seconds to stop peacefully
                self.slave_process.join(5.0)
                if self.slave_process.is_alive():
                    self.slave_process.terminate()
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
        new_key = 'AutoProxy_key_' + str(id(original_object))
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
            for k, v in value.iteritems():
                r[k] = self.objects_to_keys(v)
            return r
        else:
            # some other type that has to be accessed by proxy
            #  because it may not be picklable
            if callable(value):
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
            for k, v in value.iteritems():
                r[k] = self.keys_to_objects(v)
            return r
        elif t is pythics.libproxy.FunctionProxy:
            name = value.name
            return lambda *args, **kwargs: self.exec_master_to_slave_call_request(name)
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
            self.slave_to_master_call_return_queue.put(cpe)
            # re-raise exception in this process
            raise
        else:
            self.slave_to_master_call_return_queue.put(ret)
        finally:
            self.slave_to_master_call_queue_semaphore.release()

    def get_Proxy_attr(self, proxy_key, name):
        try:
            r = getattr(self.lookup(proxy_key), name)
            ret = self.objects_to_keys(r)
        except Exception as e:
            cpe = pythics.libproxy.CrossProcessExceptionProxy(str(e))
            self.slave_to_master_call_return_queue.put(cpe)
            # re-raise exception in this process
            raise
        else:
            self.slave_to_master_call_return_queue.put(ret)
        finally:
            self.slave_to_master_call_queue_semaphore.release()

    def set_Proxy_attr(self, proxy_key, name, value):
        try:
            v = self.keys_to_objects(value)
            setattr(self.lookup(proxy_key), name, v)
        except Exception:
            logger = multiprocessing.get_logger()
            logger.exception('Exception raised in master thread that cannot propagate to action process.')
            # re-raise exception in this process
            raise
        finally:
            self.slave_to_master_call_queue_semaphore.release()

    def call_Proxy_method(self, proxy_key, method_name, *args, **kwargs):
        try:
            a = self.keys_to_objects(args)
            kwa = self.keys_to_objects(kwargs)
            r = getattr(self.lookup(proxy_key), method_name)(*a, **kwa)
            ret = self.objects_to_keys(r)
        except Exception as e:
            cpe = pythics.libproxy.CrossProcessExceptionProxy(str(e))
            self.slave_to_master_call_return_queue.put(cpe)
            # re-raise exception in this process
            raise
        else:
            self.slave_to_master_call_return_queue.put(ret)
        finally:
            self.slave_to_master_call_queue_semaphore.release()

    def call_Proxy_method_no_return(self, proxy_key, method_name, *args, **kwargs):
        try:
            a = self.keys_to_objects(args)
            kwa = self.keys_to_objects(kwargs)
            getattr(self.lookup(proxy_key), method_name)(*a, **kwa)
        except Exception:
            logger = multiprocessing.get_logger()
            logger.exception('Exception raised in master thread that cannot propagate to action process.')
            # re-raise exception in this process
            raise
        finally:
            self.slave_to_master_call_queue_semaphore.release()

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
            logger.exception('Exception raised in master thread that cannot propagate to action process.')
            # re-raise exception in this process
            raise
        finally:
            self.slave_to_master_call_queue_semaphore.release()

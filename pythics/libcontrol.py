# -*- coding: utf-8 -*-
#
# Copyright 2008 - 2013 Brian R. D'Urso
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
import collections


#
# base class for controls
#
class Control(object):
    def __init__(self, parent, actions={}, save=True, user=None):
        self._parent = parent
        self._widget = None
        self._blocked = False
        self.actions = actions
        self._enabled = True
        self.save = save
        if user is not None:
            self.user = user
        else:
            self.user = None

    def _register(self, process, element_id, proxy_key):
        self._element_id = element_id
        self._process = process
        self._proxy_key = proxy_key
        # setup Qt signals and slots from the actions dictionary
        self._connect_actions()
        # define self._proxy only if you want a custom proxy
        #self._proxy = None

    # use _block_signals() with __enter__ and __exit__ methods to block
    # actions triggered by programatically triggered changes. Use like:
    # with self._block_signals():
    #   do_something()
    def _block_signals(self):
        return self

    def __enter__(self, *args, **kwargs):
        self._blocked = True

    def __exit__(self, *args, **kwargs):
        self._blocked = False

    def _redraw(self):
        # called when extra control redraws are needed
        pass

    def _get_parameter(self):
        return None

    def _set_parameter(self, value):
        pass

    def _connect_actions(self):
        for k in self.actions:
            getattr(self._widget, k).connect(lambda: self._exec_action(k))

    def _exec_action(self, k):
        if self.enabled and (not self._blocked):
            if k in self.actions:
                self._process.exec_master_to_slave_call_request(self.actions[k])

    def _get_enabled(self):
        return self._enabled

    def _set_enabled(self, value):
        self._widget.setEnabled(value)
        self._enabled = value

    enabled = property(_get_enabled, _set_enabled, doc=\
        """This property holds whether the control is enabled.

        If *enabled* is True, the control handles keyboard and mouse events.
        If *enabled* is False, the control does not handle these events and may
        be displayed differently.
        """)

    def _dir(self):
        out = list()
        for item in dir(self):
            if not item.startswith('_'):
                out.append(item)
        return out


#
# base class for Matplotlib controls with modified setup of events
#
class MPLControl(Control):
    def __init__(self, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        # event handling
        #
        # a deque to act as a FIFO queue for events
        #   add an event with self.events.appendleft()
        #   get an event with self.events.pop()
        self._events = collections.deque()

    def _connect_actions(self):
        for k in self.actions:
            def f(event):
                self._events.appendleft(event)
                self._exec_action(k)
            self._mpl_widget.mpl_connect(k, f)

    def _get_events(self):
        return self._events

    events = property(_get_events, doc=\
        """This read-only property holds a deque of event information.

        For each matplotlib event that occurs with an assigned action, an entry
        will be added to the deque. The action should retrieve the event
        information with events.pop().
        """)

# THIS MAY NOT BE NEEDED ANYMORE
def str_to_bool(string):
    if type(string) == bool:
        return string
    else:
        if string not in ['True', 'False']:
            raise TypeError("value should be 'True' or 'False'")
        if string == 'True':
            return True
        else:
            return False

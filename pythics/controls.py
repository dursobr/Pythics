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
import ctypes
import importlib
import multiprocessing
import os.path
import io as StringIO

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

import pythics.html
import pythics.libcontrol
import pythics.control_helpers
import pythics.proxies
import pythics.meter


#
# Main
#   Multi-function control for functions wihtout a persistent widget
#
class Main(pythics.libcontrol.Control):
    """Multi-function control for functions wihtout a persistent widget. This 
    control is used to import Python file for use by the app process, to load 
    parameters from a file or save them to a file, and to pop up file, message,
    and other dialog boxes.

    HTML parameters:

      *python_filename*: str
        name of the python file to import with no extension

      *parameters_filename*: str
        name of the file to load parameters from

      *label*: [ str | *None* (default) ]
        text to show in GUI or None to show nothing in GUI for this control

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'initialized'       python script is loaded
        'terminated'        python script is closed
        ================    ===================================================
    """

    def __init__(self, parent, python_filename='', parameters_filename='', label=None, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        if label is None or label == '':
            self._widget = None
        else:
            self._widget = QtWidgets.QLabel(label)
        self._python_filename = python_filename
        self._parameters_filename = parameters_filename

    def _register(self, process, element_id, proxy_key):
        self._element_id = element_id
        self._process = process
        self._proxy_key = proxy_key
        self._process.append_module_name(self._python_filename)
        if 'initialized' in self.actions:
            self._process.append_initialization_command(self.actions['initialized'])
        if 'terminated' in self.actions:
            self._process.append_termination_command(self.actions['terminated'])
        process.default_parameter_filename = self._parameters_filename
        process.load_parameters()

    def import_module(self, module):
        return importlib.import_module(module)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def load_parameters(self, filename=None):
        """Load parameters from a file. Use default parameter file if filename=None."""
        self._process.load_parameters(filename)

    def save_parameters(self, filename=None):
        """Save current parameters to a file. Use default parameter file if filename=None."""
        self._process.save_parameters(filename)

    def open_input_dialog_int(self, title, message, default_value=0, minimum=-2147483647, maximum=2147483647, step=1):
        """Open a dialog box for the user to enter an integer value."""
        ret = QtWidgets.QInputDialog.getInt(self._parent, title, message,
                                            default_value, minimum, maximum, step)
        return ret

    def open_input_dialog_double(self, title, message, default_value=0.0, minimum=-3.402823466E+38, maximum=3.402823466E+38, decimals=1):
        """Open a dialog box for the user to enter a double-precision floating point value."""
        ret = QtWidgets.QInputDialog.getDouble(self._parent, title, message,
                                               default_value, minimum, maximum, decimals)
        return ret

    def open_input_dialog_item(self, title, message, items=[], default_item=0, editable=True):
        """Open a dialog box for the user to choose one or more items from a list."""
        ret = QtWidgets.QInputDialog.getItem(self._parent, title, message,
                                             items, default_item, editable)
        return ret

    def open_input_dialog_text(self, title, message, default_value=''):
        """Open a dialog box for the user to enter a string."""
        ret = QtWidgets.QInputDialog.getText(self._parent, title, message,
                                             QtWidgets.QLineEdit.Normal, default_value)
        return ret

    def open_message_dialog(self, title, message, severity,
                    ok_button=True, cancel_button=False, yes_button=False,
                    no_button=False, abort_button=False, retry_button=False,
                    ignore_button=False):
        """Pops up a message box with a choice of buttons.

        Arguments:

          *title*: str (default 'MessageDialog')
            string to display as title of message box

          *message*: str (default '')
            string to display in message box

          *ok_button*: [ *True* | *False* (default) ]
            whether to include an ok button

          *cancel_button*: [ *True* | *False* (default) ]
            whether to include a cancel button

          *yes_button*: [ *True* | *False* (default) ]
            whether to include a yes button

          *no_button*: [ *True* | *False* (default) ]
            whether to include a no button

          *abort_button*: [ *True* | *False* (default) ]
            whether to include an abort button

          *retry_button*: [ *True* | *False* (default) ]
            whether to include a retry button

          *ignore_button*: [ *True* | *False* (default) ]
            whether to include an ignore button

          *severity*: [ *None* (default), 'question', 'information', 'warning', or 'critical' ]
            if given, the type of message to show

          *label*: [ str | *None* (default) ]
            text to show in GUI

        Returns (bool):
          True on Ok, Yes, Retry, or Ignore; False otherwise
        """
        buttons = QtWidgets.QMessageBox.NoButton
        if ok_button:
            # An "OK" button defined with the AcceptRole.
            buttons = buttons | QtWidgets.QMessageBox.Ok
        if cancel_button:
            # A "Cancel" button defined with the RejectRole.
            buttons = buttons | QtWidgets.QMessageBox.Cancel
        if yes_button:
            # A "Yes" button defined with the YesRole.
            buttons = buttons | QtWidgets.QMessageBox.Yes
        if no_button:
            # A "No" button defined with the NoRole.
            buttons = buttons | QtWidgets.QMessageBox.No
        if abort_button:
            # An "Abort" button defined with the RejectRole.
            buttons = buttons | QtWidgets.QMessageBox.Abort
        if retry_button:
            # A "Retry" button defined with the AcceptRole.
            buttons = buttons | QtWidgets.QMessageBox.Retry
        if ignore_button:
            # An "Ignore" button defined with the AcceptRole.
            buttons = buttons | QtWidgets.QMessageBox.Ignore
        if severity == 'question':
            ret = QtWidgets.QMessageBox.question(self._parent, title, message, buttons)
        elif severity == 'information':
            ret = QtWidgets.QMessageBox.information(self._parent, title, message, buttons)
        elif severity == 'warning':
            ret = QtWidgets.QMessageBox.warning(self._parent, title, message, buttons)
        elif severity == 'critical':
            ret = QtWidgets.QMessageBox.critical(self._parent, title, message, buttons)
        else:
            msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, title, message, buttons, self._parent)
            ret = msg.exec_()
        if ((ret == QtWidgets.QMessageBox.Ok)
            or (ret == QtWidgets.QMessageBox.Yes)
            or (ret == QtWidgets.QMessageBox.Retry)
            or (ret == QtWidgets.QMessageBox.Ignore)):
            return True
        else:
            return False

    def open_file_dialog_open_file(self, title='Choose a File', directory='', filter='*.*'):
        """Open a dialog box for the user to choose a file to open."""
        filename = QtWidgets.QFileDialog.getOpenFileName(self._parent, title, directory, filter)[0]
        return filename

    def open_file_dialog_save_file(self, title='Choose a File', directory='', filter='*.*'):
        """Open a dialog box for the user to choose a filname for saving."""
        filename = QtWidgets.QFileDialog.getSaveFileName(self._parent, title, directory, filter)[0]
        return filename

    def open_file_dialog_directory(self, title='Choose a Directory', directory=''):
        """Open a dialog box for the user to choose a directory."""
        filename = QtWidgets.QFileDialog.getExistingDirectory(self._parent, title, directory)
        return filename


#
# GlobalNamespace
#   a dummy control to create a global namespace
#   proxy class is created by multiprocessing manager
#
class GlobalNamespace(pythics.libcontrol.Control):
    """Creates a namespace that is shared between all apps. GlobalNamespaces in
    different apps with the same `id` attribute will share the same namespace.

    HTML parameters:

      *label*: [ str | *None* (default) ]
        text to show in GUI
    """
    def __init__(self, parent, label=None, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        if label is None or label == '':
            self._widget = None
        else:
            self._widget = QtWidgets.QLabel(label)

    def _register(self, process, element_id, proxy_key):
        self._element_id = element_id
        self._process = process
        self._proxy = self._process.new_global_namespace(element_id)


#
# GlobalAction
#   a dummy control to create a global action that can be triggered from
#   any process
#
class GlobalAction(pythics.libcontrol.Control):
    """Holds an action which can triggered by a `GlobalTrigger` control in another app.

    The `id` parameter is the name of the control and it must match the
    'action_id' of an associated `GlobalTrigger`. The GlobalAction and
    GlobalTrigger may be in different apps.

    HTML parameters:

      *label*: [ str | *None* (default) ]
        text to show in GUI

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'triggered'         associated GlobalTrigger.trigger() is called
        ================    ===================================================
    """
    def __init__(self, parent, label=None, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        if label is None or label == '':
            self._widget = None
        else:
            self._widget = QtWidgets.QLabel(label)

    def _register(self, process, element_id, proxy_key):
        self._element_id = element_id
        self._process = process
        self._proxy_key = proxy_key
        process.new_global_action(element_id, proxy_key)


#
# GlobalTrigger
#   a dummy control to create a global action that can be triggered from
#   any process
#
class GlobalTrigger(pythics.libcontrol.Control):
    """A control to trigger any `GlobalAction` with an `id` that matches the
    'action_id' paramter.

    The GlobalAction and GlobalTrigger may be in different apps.

    HTML parameters:

      *action_id*: str
        text to match to a 'GlobalAction' id

      *label*: [ str | *None* (default) ]
        text to show in GUI
    """
    def __init__(self, parent, action_id, label=None, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        if label is None or label == '':
            self._widget = None
        else:
            self._widget = QtWidgets.QLabel(label)
        self.action_id = action_id

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def trigger(self):
        """Trigger all GlobalActions with a matching `key`."""
        self._process.trigger_global_action(self.action_id)


#
# Timer
#
class Timer(pythics.libcontrol.Control):
    """A control which makes calls to an action at regular time intervals. Most
    settings are controlled in a call to `start`, which begins the timer. The
    timer can be stopped by calling the `stop` method. The timer may be started
    and stopped multiple times. Due to the mult-threaded nature of Timers, most
    control properties are read-only and can only be set by calling `start`.

    HTML parameters:

      *label*: [ str | *None* (default) ]
        text to show in GUI

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'triggered'         action is triggered
        ================    ===================================================
    """
    def __init__(self, parent, label=None, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        if label is None or label == '':
            self._widget = None
        else:
            self._widget = QtWidgets.QLabel(label)

    def _register(self, process, element_id, proxy_key):
        self._element_id = element_id
        self._process = process
        if 'triggered' in self.actions:
            action = self.actions['triggered']
        else:
            action = None
        self._proxy = pythics.proxies.TimerProxy(action)

    #-------------------------------------------------------------------
    # no methods for access by action proxy - all functionality in proxy
    #-------------------------------------------------------------------


#
# Button
#
class Button(pythics.libcontrol.Control):
    """A push or toggle button which can trigger an action.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *label*: str
        text to be displayed on the button

      *toggle*:  [*True* | *False* (default) ]
        whether the button should hold the pressed state

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'clicked'           button is clicked
        'pressed'           button is pressed
        'released'          button is released
        'toggled'           button changes state (only if toggle=True)
        ================    ===================================================
    """

    def __init__(self, parent, label='', toggle=False, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._toggle = toggle
        if self._toggle:
            self._widget = QtWidgets.QToolButton()
            self._widget.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
            self._widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                      QtWidgets.QSizePolicy.Fixed)
            self._widget.setText(label)
            self._widget.setCheckable(True)
        else:
            self._widget = QtWidgets.QPushButton(label)

    def _get_parameter(self):
        return self._widget.isChecked()

    def _set_parameter(self, value):
        with self._block_signals():
            self._widget.setChecked(value)

    #---------------------------------------
    # methods below used for access by proxy

    def _get_label(self):
        return self._widget.text()

    def _set_label(self, value):
        self._widget.setText(value)

    label = property(_get_label, _set_label, doc=\
        """Text to be displayed on the button.""")

    def _get_value(self):
        return self._widget.isChecked()

    def _set_value(self, value):
        with self._block_signals():
            self._widget.setChecked(value)

    value = property(_get_value, _set_value, doc=\
        """The state of the Button, if toggle=True.

        If *value* is True, the Button is pressed. If *value* is False, the
        Button is not pressed.
        """)


#
# CheckBox
#
class CheckBox(pythics.libcontrol.Control):
    """A button with a label and a checked or unchecked state.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *label*: str (default '')
        text to display next to the box

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'stateChanged'      state (checked/unchecked) changed
        'clicked'           button is clicked
        'pressed'           button is pressed
        'released'          button is released
        'toggled'           button changes state
        ================    ===================================================
    """
    def __init__(self, parent, label='', **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = QtWidgets.QCheckBox(label)

    def _get_parameter(self):
        return self._widget.isChecked()

    def _set_parameter(self, value):
        with self._block_signals():
            self._widget.setChecked(value)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_value(self):
        return self._widget.isChecked()

    def _set_value(self, value):
        with self._block_signals():
            self._widget.setChecked(value)

    value = property(_get_value, _set_value, doc=\
        """The state of the CheckBox.

        If *value* is True, the CheckBox is checked. If *value* is False, the
        CheckBox is not checked.
        """)


#
# ChoiceBox
#
class ChoiceBox(pythics.libcontrol.Control):
    """A control which lets you choose items from a scrollable box.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *choices*: list
        the list of items to choose from

      *style*: [ 'single' (default) | 'multiple' | 'extended' ]

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ======================    =============================================
        signal                    when emitted
        ======================    =============================================
        'itemSelectionChanged'    selection changed
        'currentItemChanged'
        'currentRowChanged'
        'currentTextChanged'
        'itemActivated'
        'itemChanged'
        'itemClicked'
        'itemDoubleClicked'
        'itemEntered'
        'itemPressed'
        ======================    =============================================
    """
    def __init__(self, parent, choices='[]', style='single', **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = QtWidgets.QListWidget()
        if style == 'single':
            self.style = QtWidgets.QAbstractItemView.SingleSelection
        elif style == 'multiple':
            self.style = QtWidgets.QAbstractItemView.MultiSelection
        elif style == 'extended':
            self.style = QtWidgets.QAbstractItemView.ExtendedSelection
        else:
            # SHOULD RAISE AN EXCEPTION
            pass
        self._widget.setSelectionMode(self.style)
        self._set_choices(choices)

    def _get_parameter(self):
        if self.style == QtWidgets.QAbstractItemView.SingleSelection:
            s = self._widget.selectedItems()
            if len(s) > 0:
                return self._widget.selectedItems()[0].text()
            else:
                return None
        else:
            selections = list()
            for i in self._widget.selectedItems():
                selections.append(i.text())
            return selections

    def _set_parameter(self, value):
        with self._block_signals():
            self._widget.clearSelection()
            if value is not None:
                if self.style == QtWidgets.QAbstractItemView.SingleSelection:
                    i = self._choices.index(value)
                    j = self._widget.item(i)
                    self._widget.setCurrentItem(j)
                else:
                    for i in range(len(self.choices)):
                        if value.count(self.choices[i]) > 0:
                            j = self._widget.item(i)
                            self._widget.setCurrentItem(j)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_value(self):
        return self._get_parameter()

    def _set_value(self, value):
        self._set_parameter(value)

    value = property(_get_value, _set_value, doc=\
        """the user's choice or choices""")

    def set_first_visible_item(self, value):
        """Move the scroll bar to set the first visible choice."""
        self._widget.SetFirstItem(value)

    def _get_choices(self):
        return self._choices

    def _set_choices(self, choices):
        self._widget.clear()
        self._choices = choices
        max_n = len(self._choices)
        for c in self._choices:
            self._widget.insertItem(max_n, c)

    choices = property(_get_choices, _set_choices, doc=\
        """the list of items to choose from""")


#
# ChoiceButton
#
class ChoiceButton(pythics.libcontrol.Control):
    """A control which lets you choose items from a popup list.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *choices*: list
        the list of items to choose from

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        =====================    ==============================================
        signal                   when emitted
        =====================    ==============================================
        'activated'              selection is made
        'currentIndexChanged'
        'editTextChanged'
        'highlighted'
        =====================    ==============================================
    """
    def __init__(self, parent, choices=[], **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = QtWidgets.QComboBox()
        self._set_choices(choices)

    def _get_parameter(self):
        return self._widget.currentText()

    def _set_parameter(self, value):
        i = self._choices.index(value)
        with self._block_signals():
            self._widget.setCurrentIndex(i)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_value(self):
        return self._get_parameter()

    def _set_value(self, value):
        self._set_parameter(value)

    value = property(_get_value, _set_value, doc=\
        """the user's choice or choices""")

    def _get_choices(self):
        return self._widget.choices

    def _set_choices(self, choices):
        self._widget.clear()
        self._choices = choices
        max_n = len(self._choices)
        for c in self._choices:
            self._widget.insertItem(max_n, c)

    choices = property(_get_choices, _set_choices, doc=\
        """the list of items to choose from""")


#
# EventButton
#
class EventButton(pythics.libcontrol.Control):
    """A push or toggle button which can trigger an action and communicate with
    your process through a multiprocessing.Event object. 
    
    EventButtons have two particularly useful features: 
    
    First, using the start_interval wait_interval methods, you can make a loop 
    repeat with a set repetition time, automatically taking account for the 
    time your code takes to run (if you just want a fixed delay, use wait()). 
    wait() and wait_interval() are interrupted if the Event is set, so long 
    waits will end immediately if signaled by the EventButton. 
    
    Second, when used as a stop or start/stop button, your code can check 
    whether stop has been requested using the is_set method, which is much 
    faster than sending a normal command to or from the GUI. This could also be
    useful if you need a button to request some kind of slow GUI update in an
    otherwise fast loop.
    
    Note that while waiting (with wait or wait_interval), no other code in your 
    process will run and new GUI actions will not be processed.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *label*: str (default '')
        text to be displayed on the button

      *toggle*: [*True* | *False*  (default) ]
        whether the button should hold the pressed state

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'clicked'           button is clicked
        'pressed'           button is pressed
        'released'          button is released
        'run'               change from unpressed to pressed (only if toggle=True)
        ================    ===================================================
    """
    def __init__(self, parent, label='', toggle=False, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._toggle = toggle
        if self._toggle:
            self._widget = QtWidgets.QToolButton()
            self._widget.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
            self._widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                      QtWidgets.QSizePolicy.Fixed)
            self._widget.setText(label)
            self._widget.setCheckable(True)
        else:
            self._widget = QtWidgets.QPushButton(label)

    def _register(self, process, element_id, proxy_key):
        self._element_id = element_id
        self._proxy_key = proxy_key
        self._process = process
        self._event = multiprocessing.Event()
        self._widget.clicked.connect(self._on_click)
        self._proxy = pythics.proxies.EventButtonProxy(self._event, proxy_key)

    def _on_click(self, *args, **kwargs):
        if self._toggle:
            if self._widget.isChecked():
                self._event.clear()
                self._exec_action('run')
            else:
                self._event.set()
                self._exec_action('clicked')
        else:
            self._event.set()
            self._exec_action('clicked')

    def _get_parameter(self):
        return self._widget.isChecked()

    def _set_parameter(self, value):
        with self._block_signals():
            self._widget.setChecked(value)

    #---------------------------------------
    # methods below used for access by proxy

    def _get_label(self):
        return self._widget.text()

    def _set_label(self, value):
        self._widget.setText(value)

    label = property(_get_label, _set_label, doc=\
        """Text to be displayed on the button.""")

    def _get_value(self):
        return self._widget.isChecked()

    def _set_value(self, value):
        with self._block_signals():
            self._widget.setChecked(value)

    value = property(_get_value, _set_value, doc=\
        """The state of the Button, if toggle=True.

        If *value* is True, the EventButton is pressed. If *value* is False, 
        the EventButton is not pressed.
        """)


#
# FilePicker: file browser with text entry box
#
class FilePicker(pythics.libcontrol.Control):
    """Text entry box for a file name or directory which can also pop up a file
    dialog box.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *label*: str (default 'File')
        label on the FilePicker widget

      *title*: str (default 'Choose')

      *directory*: str
        starting base directory

      *filter*: str (default '\*.\*')
        filter for displayed file names

      *dialog_type*: [ 'open_file' | 'save_file' (default) | 'directory' ]

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'textChanged'       file is selected
        ================    ===================================================
    """
    def __init__(self, parent, label='File', title='Choose', directory='',
                 filter='*.*', dialog_type='save', **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = QtWidgets.QGroupBox(label)
        self.type = dialog_type
        self.title = title
        self.directory = directory
        self.filter = filter
        hbox = QtWidgets.QHBoxLayout()
        self._text_box = QtWidgets.QTextEdit()
        hbox.addWidget(self._text_box)
        self._button = QtWidgets.QPushButton('Browse')
        hbox.addWidget(self._button)
        self._widget.setLayout(hbox)
        # set default height
        self._widget.setFixedHeight(65)
        self._button.clicked.connect(self.browse)

    def _register(self, process, element_id, proxy_key):
        self._element_id = element_id
        self._process = process
        self._proxy_key = proxy_key
        # setup Qt signals and slots from the actions dictionary
        self._text_box.textChanged.connect(lambda: self._exec_action('textChanged'))

    def _get_parameter(self):
        return self._text_box.toPlainText()

    def _set_parameter(self, value):
        with self._block_signals():
            self._text_box.setPlainText(value)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_value(self):
        return self._get_parameter()

    def _set_value(self, value):
        self._set_parameter(value)

    value = property(_get_value, _set_value, doc=\
        """the user's choice of filename or directory""")

    def browse(self):
        """Open the file dialog box."""
        if self.type == 'open_file':
            filename = QtWidgets.QFileDialog.getOpenFileName(self._parent, self.title,
                                             self.directory, self.filter)[0]
        elif self.type == 'directory':
            filename = QtWidgets.QFileDialog.getExistingDirectory(self._parent,
                self.title, self.directory, QtWidgets.QFileDialog.ShowDirsOnly)
        else:
            filename = QtWidgets.QFileDialog.getSaveFileName(self._parent, self.title,
                                             self.directory, self.filter)[0]
        filename = filename
        self._text_box.setPlainText(filename)
        return filename


#
# Image: scrolled image canvas
#
class Image(pythics.libcontrol.Control):
    """Displays an image. The image can be dynamically updated and mouse interaction
    is possible.

    HTML parameters:

      *fit*: [ *True* | *False* (default) ]
        whether to resize the image to fit in the widget

      *scale*: float (default 1.0)
        scaling for image

      *use_shared_memory*: [ *True* | *False* (default) ]
        whether to use shared memory for faster updates (fixed max image size)

      *image_dimensions*: [ tuple | *None* ]
        specify maximum image size, requred if 'use_shared_memory' is *True*

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        =======================    ============================================
        signal                     when emitted
        =======================    ============================================
        'mouseLeftPress'           mouse left button pressed
        'mouseLeftRelease'         mouse left button released
        'mouseLeftDoubleClick'     mouse left button double clicked
        'mouseRightPress'          mouse right button pressed
        'mouseRightRelease'        mouse right button released
        'mouseRightDoubleClick'    mouse right button double clicked
        =======================    ============================================
    """
    def __init__(self, parent, fit=False, scale=1.0, use_shared_memory=False,
                    image_dimensions=None, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._image_size = (0, 0)
        self._last_image_size = self._image_size
        self._use_shared_memory = use_shared_memory
        if self._use_shared_memory:
            dim = image_dimensions
            self._image_size = (int(dim[0]), int(dim[1]))
            self._image_max_size = self._image_size
        self._pixmap = None
        self._fit = fit
        self._scale = scale
        self._image_label = pythics.control_helpers.ImageLabel(self)
        self._image_label.setBackgroundRole(QtGui.QPalette.Dark)
        self._image_label.setFit(self._fit)
        self._image_label.setScale(self._scale)
        self._widget = QtWidgets.QScrollArea()
        self._widget.setBackgroundRole(QtGui.QPalette.Dark)
        self._widget.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self._widget.setWidget(self._image_label)
        self._widget.setWidgetResizable(self._fit)
        self.left_press_position = None
        self.right_press_position = None
        self.left_release_position = None
        self.right_release_position = None
        self.left_double_click_position = None
        self.right_double_click_position = None
        # color table for greyscale indexed images
        self.greyscale_color_table = [QtGui.qRgb(i, i, i) for i in range(256)]

    def _adjust_scroll_bar(scroll_bar, factor):
        scroll_bar.setValue(int(factor * scroll_bar.value()
                             + ((factor - 1) * scroll_bar.pageStep()/2.0)))

    def _display_image(self):
        self._image_label.setImage(self.image)

    def _mouse_press_left(self, x, y):
        self.left_press_position = (x, y)
        self._exec_action('mouseLeftPress')

    def _mouse_press_right(self, x, y):
        self.right_press_position = (x, y)
        self._exec_action('mouseRightPress')

    def _mouse_release_left(self, x, y):
        self.left_release_position = (x, y)
        self._exec_action('mouseLeftRelease')

    def _mouse_release_right(self, x, y):
        self.right_release_position = (x, y)
        self._exec_action('mouseRightRelease')

    def _mouse_double_click_left(self, x, y):
        self.left_double_click_position = (x, y)
        self._exec_action('mouseLeftDoubleClick')

    def _mouse_double_click_right(self, x, y):
        self.right_double_click_position = (x, y)
        self._exec_action('mouseRightDoubleClick')

    def _get_parameter(self):
        return None
        #if self._use_shared_memory:
        #    w, h = self._image_size
        #    return self.shared_image_data.raw[0:(4*w*h)], (w, h)
        #else:
        #    return self.image_data, self._image_size

    def _set_parameter(self, value):
        pass
        #data, size = value
        #w, h = size
        #if self._use_shared_memory:
        #    self.shared_image_data.raw[0:(4*w*h)] = data
        #else:
        #    self.image_data = data
        #self._image_size = size
        #self.image = QtGui.QImage(data, w, h, QtGui.QImage.Format_ARGB32)
        #self._display_image()

    def _register(self, process, element_id, proxy_key):
        # custom _register since actions have to be spread over buttons
        self._element_id = element_id
        self._process = process
        self._proxy_key = proxy_key
        if self._use_shared_memory:
            # need 4 chars per pixel for RGBA values
            size = 4*self._image_max_size[0]*self._image_max_size[1]
            self.shared_image_data = multiprocessing.Array(ctypes.c_char, size)
            #size = 4*self._image_max_size[0]*self._image_max_size[1]
            #self.shared_image_data = multiprocessing.Array(ctypes.c_int8, size)
            self._proxy = pythics.proxies.ImageWithSharedProxy(self.shared_image_data, proxy_key)
        else:
            self._proxy = pythics.proxies.ImageProxy(proxy_key)

    #---------------------------------------
    # used for access by either action proxy

    def _set_fit(self, fit):
        self._image_label.setFit(False)
        self._fit = fit

    def _get_fit(self):
        return self._fit

    fit = property(_get_fit, _set_fit, doc=\
        """Whether to resize the image to fit in the widget.""")

    def _set_scale(self, scale):
        self._image_label.setFit(False)
        self._image_label.setScale(scale)
        self._adjust_scroll_bar(self.scroll_area.horizontalScrollBar(), scale/self._scale)
        self._adjust_scroll_bar(self.scroll_area.verticalScrollBar(), scale/self._scale)
        self._scale = scale

    def _get_scale(self):
        return self._scale

    scale = property(_get_scale, _set_scale, doc=\
        """A floating point value specifying the scaling of the image""")

    #--------------------------------------------------------------------
    # used only for access by action proxy with 'use_shared_memory=False'

#    def _get_image(self):
#        return self.image_data, self._image_size
#
#    def _set_image(self, data, size):
#        self.image_data = data
#        self._image_size = size
#        w, h = size
#        self.image = QtGui.QImage(data, w, h, QtGui.QImage.Format_ARGB32)
#        self._display_image()

    def _display(self, mode, size, data):
        self.image_data = data
        self._image_size = size
        w, h = size
        if mode == 'L':
            self.image = QtGui.QImage(data, w, h, w, QtGui.QImage.Format_Indexed8)
            self.image.setColorTable(self.greyscale_color_table)
        elif mode == 'RGB':
            self.image = QtGui.QImage(data, w, h, 3*w, QtGui.QImage.Format_RGB888)
        elif mode == 'ARGB':
            self.image = QtGui.QImage(data, w, h, 4*w, QtGui.QImage.Format_ARGB32)
        self._display_image()

    #-------------------------------------------------------------------
    # used only for access by action proxy with 'use_shared_memory=True'

#    def _get_image_with_shared(self):
#        return self._image_size
#
#    def _set_image_with_shared(self, size):
#        w, h = size
#        self._image_size = size
#        self.shared_image_data_subset = self.shared_image_data.raw[0:(4*w*h)]
#        self.image = QtGui.QImage(self.shared_image_data_subset,
#                                    w, h, QtGui.QImage.Format_ARGB32)
#        self._display_image()

    def _display_shared(self, mode, size):
        w, h = size
        self._image_size = size

        if mode == 'L':
            self.shared_image_data_subset = self.shared_image_data.raw[0:(w*h)]
            self.image = QtGui.QImage(self.shared_image_data_subset,
                                      w, h, w, QtGui.QImage.Format_Indexed8)
            self.image.setColorTable(self.greyscale_color_table)
        elif mode == 'RGB':
            self.shared_image_data_subset = self.shared_image_data.raw[0:(3*w*h)]
            self.image = QtGui.QImage(self.shared_image_data_subset,
                                      w, h, 3*w, QtGui.QImage.Format_RGB888)
        elif mode == 'ARGB':
            self.shared_image_data_subset = self.shared_image_data.raw[0:(4*w*h)]
            self.image = QtGui.QImage(self.shared_image_data_subset,
                                      w, h, 4*w, QtGui.QImage.Format_ARGB32)
        self._display_image()


#
# ImageButton: button with image as label
#
class ImageButton(pythics.libcontrol.Control):
    """A button with an image as a label and possible change in image when pressed.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *toggle*: [ *True* | *False* (default) ]

      *image_filename*: str (default *None*)
        name of image file to display on button

      *pressed_image_filename*: str (default *None*)
        name of image file to display on button when pressed

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'clicked'           button is clicked
        'pressed'           button is pressed
        'released'          button is released
        'toggled'           button changes state (only if toggle=True)
        ================    ===================================================
    """
    def __init__(self, parent, toggle=False, image_filename=None,
                 pressed_image_filename=None, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = QtWidgets.QToolButton()
        self._widget.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        if image_filename is not None:
            if not os.path.isfile(image_filename):
                image_filename = os.path.join(self._process.path, image_filename)
            self._pixmap = QtGui.QPixmap(image_filename)
            self._widget.setIconSize(self._pixmap.size())
            self._icon = QtGui.QIcon(self._pixmap)
            self._widget.setIcon(self._icon)
        if pressed_image_filename is not None:
            if not os.path.isfile(pressed_image_filename):
                pressed_image_filename = os.path.join(self._process.path, pressed_image_filename)
            self._pressed_pixmap = QtGui.QPixmap(pressed_image_filename)
            self._pressed_icon = QtGui.QIcon(self._pressed_pixmap)
        else:
            self._pressed_icon = None
        self._toggle = toggle
        if self._toggle:
            self._widget.setCheckable(True)
        else:
            self._widget.setCheckable(False)
        if pressed_image_filename is not None:
            self._widget.pressed.connect(self._pressed)
            self._widget.released.connect(self._released)

    def _pressed(self):
        if self._pressed_icon is not None:
            self._widget.setIcon(self._pressed_icon)

    def _released(self):
        if (self._pressed_icon is not None) and (not self._widget.isChecked()):
            self._widget.setIcon(self._icon)
#            else:
#                self._widget.setIcon(self._icon)

    def _get_parameter(self):
        return self._widget.isChecked()

    def _set_parameter(self, value):
        with self._block_signals():
            self._widget.setChecked(value)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_value(self):
        return self._widget.isChecked()

    def _set_value(self, value):
        with self._block_signals():
            self._widget.setChecked(value)
            if value:
                self._widget.setIcon(self._pressed_icon)
            else:
                self._widget.setIcon(self._icon)

    value = property(_get_value, _set_value, doc=\
        """The state of the ImageButton, if toggle=True.

        If *value* is True, the ImageButton is pressed. If *value* is False, the
        ImageButton is not pressed.
        """)


#
# Knob
#
class Knob(pythics.libcontrol.Control):
    """A multiturn dial that can be rotated to select one value out of a list
    of values.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *choices*: list
        the list of items to choose from

      *steps*: in (default 50)
        how many steps per turn of the dial

      *acceleration*: float (default 5.0)
        controls how much to accelerate value if know is turned quickly, set to
        0 to disable acceleration

      *tracking*: [ *True* | *False* (default) ]
        whether to emit many 'choiceChanged' events as the knob is dragged

      *wrapping*: [ *True* | *False* (default) ]
        whether the values start over after one revolution

      *prefix*: str (default '')
        string to display on the knob before the value

      *suffix*: str (default '')
        string to display on the knob after the value

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'choiceChanged'      the value has changed,
                              tracking determines whether this signal is
                              emitted during user interaction
        'sliderPressed'     the user starts to drag the knob
        'sliderMoved'       the user drags the knob
        'sliderReleased'    the user releases the knob.
        ================    ===================================================
    """
    def __init__(self, parent, choices=['None'], steps=50, acceleration=5.0,
                 tracking=False, wrapping=False, prefix='', suffix='', **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = pythics.control_helpers.Knob(choices=list(choices),
                                                    steps=steps,
                                                    acceleration=acceleration,
                                                    tracking=tracking,
                                                    wrapping=wrapping,
                                                    prefix=prefix,
                                                    suffix=suffix)

    def _get_parameter(self):
        return self._widget.getChoiceValue()

    def _set_parameter(self, value):
        with self._block_signals():
            self._widget.setChoiceValue(value)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_choices(self):
        return self._widget.getChoices()

    def _set_choices(self, value):
        with self._block_signals():
            self._widget.setChoices(list(value))

    choices = property(_get_choices, _set_choices, doc=\
        """The list of items to choose from.
        """)

    def _get_prefix(self):
        return self._widget.prefix

    def _set_prefix(self, value):
        with self._block_signals():
            self._widget.prefix = value
            self._widget.update()

    prefix = property(_get_prefix, _set_prefix, doc=\
        """The prefix diplayed on the knob.
        """)

    def _get_suffix(self):
        return self._widget.suffix

    def _set_suffix(self, value):
        with self._block_signals():
            self._widget.suffix = value
            self._widget.update()

    suffix = property(_get_suffix, _set_suffix, doc=\
        """The suffix diplayed on the knob.
        """)

    def _get_value(self):
        return self._widget.getChoiceValue()

    def _set_value(self, value):
        with self._block_signals():
            self._widget.setChoiceValue(value)

    value = property(_get_value, _set_value, doc=\
        """The current value selected on the knob.
        """)


#
# Meter
#
class Meter(pythics.libcontrol.Control):
    """Displays a panel meter with a needle pointing to a value on a scale.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *minimum*: [ int | float ] (default *0*)
        minimum scale value

      *maximum*: [ int | float ] (default *100*)
        maximim scale value

      *fmt*: [ str ] (default *f*)
        format specifier for labels

      *precision*: [ int ] (default *0*)
        nunber of digits in labels after the decimal point
    """
    def __init__(self, parent, minimum=0.0, maximum=100.0, fmt='f', precision=0, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = pythics.meter.QMeter()
        self._minimum = minimum
        self._maximum = maximum
        self._widget.setRange(minimum, maximum)
        self._fmt = fmt
        self._precision = precision
        self._widget.setLabelsFormat(fmt, precision)

    def _get_parameter(self):
        return self._widget.value()

    def _set_parameter(self, value):
        with self._block_signals():
            self._widget.setValue(value)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_minimum(self):
        return self._minimum

    def _set_minimum(self, value):
        self._minimum = value
        with self._block_signals():
            self._widget.setRange(self._minimum, self._maximum)

    minimum = property(_get_minimum, _set_minimum, doc=\
        """The minimum scale value displayed.
        """)

    def _get_maximum(self):
        return self._maximum

    def _set_maximum(self, value):
        self._maximum = value
        with self._block_signals():
            self._widget.setRange(self._minimum, self._maximum)

    maximum = property(_get_maximum, _set_maximum, doc=\
        """The maximum scale value displayed.
        """)

    def _get_precision(self):
        return self._precision

    def _set_precision(self, value):
        self._precision = value
        with self._block_signals():
            self._widget.setLabelsFormat(self._fmt, self._precision)

    precision = property(_get_precision, _set_precision, doc=\
        """The nunber of digits in labels after the decimal point.
        """)

    def _get_value(self):
        return self._widget.value()

    def _set_value(self, value):
        with self._block_signals():
            self._widget.setValue(value)

    value = property(_get_value, _set_value, doc=\
        """The value indicated by the needle on the meter.
        """)


#
# MetricNumBox
#
class MetricNumBox(pythics.libcontrol.Control):
    """A box for entering and displaying floating point values with metric units.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *read_only*: [ *True* | *False* (default) ]
        if *True*, number cannot be edited by user

      *align*: [ 'left' (default) | 'center' | 'right' ]
        justfication of displayed value

      *increment*: [ int | float ] (default 1)
        how much to change the value by when an up or down button is pushed

      *format_str*: str (default '%g')
        printf style format string used to format number if 'notation' is 'scientific'

      *font_size*: int (default None)
        font size to use for numeric display, use system default if not given

      *maximum*: [ int | float ] (default *None*)
        maximim allowed value, if given

      *minimum*: [ int | float ] (default *None*)
        minimum allowed value, if given

      *prefix*: str (default '')
        text to show before the value, e.g. '$'

      *base_unit*: str (default '')
        base unit to be shown after the value; the metric prefix will be added

      *metric_prefix:: str (default '')
        the default metric prefix

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'valueChanged'      value is changed
        ================    ===================================================
    """
    def __init__(self, parent,
                 read_only = False, align='left',
                 increment=1, digits=1,
                 notation='decimal', format_str='%g',
                 maximum=None, minimum=None,
                 prefix='', base_unit='', metric_prefix='', font_size=None,
                 **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._digits = digits
        self._notation = notation
        self._format_str = format_str
        self._widget = pythics.control_helpers.MetricDoubleSpinBox(format_str=self._format_str, base_unit=base_unit, metric_prefix=metric_prefix)
        self._widget.setKeyboardTracking(False)
        # set to maximum precision, otherwise values get rounded
        self._widget.setDecimals(323)
        self._widget.setSingleStep(increment)
        if minimum is not None:
            self._widget.setMinimum(minimum)
        else:
            # MetricDoubleSpinBox needs a minimum, so make it large
            self._widget.setMinimum(-1e300)
        if maximum is not None:
            self._widget.setMaximum(maximum)
        else:
            # MetricDoubleSpinBox needs a maximum, so make it large
            self._widget.setMaximum(1e300)
        if read_only:
            self._widget.setReadOnly(True)
            self._widget.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        if align == 'right':
            self._alignment = QtCore.Qt.AlignRight
        elif align == 'center':
            self._alignment = QtCore.Qt.AlignHCenter
        else:
            self._alignment = QtCore.Qt.AlignLeft
        self._widget.setAlignment(self._alignment)
        self._widget.setPrefix(prefix)
        # set default height to approximately 1 line of text
        metrics = self._widget.fontMetrics()
        self._widget.setFixedHeight(1.8*metrics.lineSpacing())
        if font_size is not None:
            f = self._widget.font()
            f.setPointSize(font_size)
            self._widget.setFont(f)

    def _get_parameter(self):
        return float(self._widget.value())

    def _set_parameter(self, value):
        with self._block_signals():
            self._widget.setValue(value)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_value(self):
        return self._get_parameter()

    def _set_value(self, value):
        self._set_parameter(value)

    value = property(_get_value, _set_value, doc=\
        """The numerical value entered in the base unit.""")



#
# NumBox
#
class NumBox(pythics.libcontrol.Control):
    """A box for entering and displaying integers and floats.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *read_only*: [ *True* | *False* (default) ]
        if *True*, number cannot be edited by user

      *align*: [ 'left' (default) | 'center' | 'right' ]
        justfication of displayed value

      *increment*: [ int | float ] (default 1)
        how much to change the value by when an up or down button is pushed

      *digits*: int (default 1)
        number of digits to show after the decimal point

      *notation*: [ 'decimal' (default) | 'scientific' ]
        how to enter and display numbers. 'scientific' enables
        scientific notation and formats the number according to 'format_str'

      *format_str*: str (default '%g')
        printf style format string used to format number if 'notation' is 'scientific'

      *font_size*: int (default None)
        font size to use for numeric display, use system default if not given

      *maximum*: [ int | float ] (default *None*)
        maximim allowed value, if given

      *minimum*: [ int | float ] (default *None*)
        minimum allowed value, if given

      *prefix*: str (default '')
        text to show before the value, e.g. '$'

      *suffix*: str (default '')
        text to show after the value, e.g. a unit

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'valueChanged'      value is changed
        ================    ===================================================
    """
    def __init__(self, parent,
                 read_only = False, align='left',
                 increment=1, digits=1,
                 notation='decimal', format_str='%g',
                 maximum=None, minimum=None,
                 prefix='', suffix='', font_size=None,
                 **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._digits = digits
        self._notation = notation
        self._format_str = format_str
        if self._notation == 'scientific':
                self._widget = pythics.control_helpers.ScientificDoubleSpinBox(format_str=self._format_str)
                self._widget.setKeyboardTracking(False)
                # set to maximum precision, otherwise values get rounded
                self._widget.setDecimals(323)
                self._widget.setSingleStep(increment)
                if minimum is not None:
                    self._widget.setMinimum(minimum)
                else:
                    # QDoubleSpinBox needs a minimum, so make it large
                    self._widget.setMinimum(-1e300)
                if maximum is not None:
                    self._widget.setMaximum(maximum)
                else:
                    # QDoubleSpinBox needs a maximum, so make it large
                    self._widget.setMaximum(1e300)
        else:
            if self._digits == 0:
                self._widget = QtWidgets.QSpinBox()
                self._widget.setKeyboardTracking(False)
                self._widget.setSingleStep(increment)
                if minimum is not None:
                    self._widget.setMinimum(minimum)
                else:
                    # QSpinBox needs a minimum, so make it large
                    self._widget.setMinimum(-99999999)
                if maximum is not None:
                    self._widget.setMaximum(maximum)
                else:
                    # QSpinBox needs a maximum, so make it large
                    self._widget.setMaximum(99999999)
            else:
                self._widget = QtWidgets.QDoubleSpinBox()
                self._widget.setKeyboardTracking(False)
                self._widget.setDecimals(digits)
                self._widget.setSingleStep(increment)
                if minimum is not None:
                    self._widget.setMinimum(minimum)
                else:
                    # QDoubleSpinBox needs a minimum, so make it large
                    self._widget.setMinimum(-99999999)
                if maximum is not None:
                    self._widget.setMaximum(maximum)
                else:
                    # QDoubleSpinBox needs a maximum, so make it large
                    self._widget.setMaximum(99999999)
        if read_only:
            self._widget.setReadOnly(True)
            self._widget.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        if align == 'right':
            self._alignment = QtCore.Qt.AlignRight
        elif align == 'center':
            self._alignment = QtCore.Qt.AlignHCenter
        else:
            self._alignment = QtCore.Qt.AlignLeft
        self._widget.setAlignment(self._alignment)
        self._widget.setPrefix(prefix)
        self._widget.setSuffix(suffix)
        # set default height to approximately 1 line of text
        metrics = self._widget.fontMetrics()
        self._widget.setFixedHeight(1.8*metrics.lineSpacing())
        if font_size is not None:
            f = self._widget.font()
            f.setPointSize(font_size)
            self._widget.setFont(f)

    def _get_parameter(self):
        if self._digits == 0:
            return int(self._widget.value())
        else:
            return float(self._widget.value())

    def _set_parameter(self, value):
        with self._block_signals():
            self._widget.setValue(value)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_value(self):
        return self._get_parameter()

    def _set_value(self, value):
        self._set_parameter(value)

    value = property(_get_value, _set_value, doc=\
        """The numerical value entered.""")


##
## NumGrid
##
#class NumGrid(pythics.libcontrol.Control):
#    def __init__(self, parent, action=None, id='', save=True,
#                 read_only = False, align='left', format='%f',
#                 **kwargs):
#        pythics.libcontrol.Control.__init__(self, parent,
#                                            action=action,
#                                            id=id,
#                                            save=save)
#        self.read_only = read_only
#        self.table = pythics.libcontrol.NumGridTable(format)
#        self._widget = wx.grid.Grid(parent, id=wx.ID_ANY, **kwargs)
#        self._widget.SetTable(self.table, False)
#        self._widget.EnableEditing(not self.read_only)
#        if align == 'right':
#            h_align = wx.ALIGN_RIGHT
#        elif align == 'center':
#            h_align = wx.ALIGN_CENTRE
#        else:
#            h_align = wx.ALIGN_LEFT
#        self._widget.SetDefaultCellAlignment(h_align, wx.ALIGN_BOTTOM)
#        if action is not None:
#            self._widget.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.run_action)

#    def _get_parameter(self):
#        return self.table.data

#    def _set_parameter(self, value):
#        if self.table.data.shape == value.shape:
#            self.table.data = value
#            self._widget.ForceRefresh()
#        else:
#            self.table.data = value
#            # is there a better way to get the table size updated than this?
#            self._widget.SetTable(self.table, False)
#            self._widget.ForceRefresh()

#    def generate_proxy(self, *args):
#        return pythics.proxies_old.NumGridProxy(*args)

#    #---------------------------------------------------
#    # methods below used only for access by action proxy

#
#    def _get_value(self):
#        return self._get_parameter()

#
#    def _set_value(self, value):
#        self._set_parameter(value)

#    ## add selection get/set, row/col labels, edit_action, select_action

#    #@pythics.libcontrol.proxy
#    #def get_selection(self):
#    #    return self._widget.GetRange()
#    #
#    #def set_selection(self, value):
#    #    self._widget.SetRange(int(value))


#
# RadioButtonBox
#
class RadioButtonBox(pythics.libcontrol.Control):
    """A collection of radio buttons.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *label*: [ str | *None* (default) ]
        text to show to label group of radio buttons

      *rows*: int (default *None*)
        if given, distribute radio buttons over this number of rows

      *columns*: int (default *None*)
        if given, distribute radio buttons over this number of columns

      *choices*: list (default [])
        list of choices to display, with one radio button per choice

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'clicked'           button is clicked
        'toggled'           button changes state
        ================    ===================================================
    """
    def __init__(self, parent, label='', rows=None, columns=None, choices=[],
                 **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        if rows is not None:
            by_row = True
            major_dimension = rows
        else:
            by_row = False
            major_dimension = columns
        self._widget = QtWidgets.QGroupBox(label)
        self._choices = choices
        self._grid = QtWidgets.QGridLayout()
        self._buttons = list()
        major = 0
        minor = 0
        for c in self._choices:
            rb = QtWidgets.QRadioButton(c)
            self._buttons.append(rb)
            if by_row:
                self._grid.addWidget(rb, major, minor)
            else:
                self._grid.addWidget(rb, minor, major)
            major += 1
            if major == major_dimension:
                major = 0
                minor += 1
        self._buttons[0].setChecked(True)
        self._widget.setLayout(self._grid)

    def _register(self, process, element_id, proxy_key):
        # custom _register since actions have to be spread over buttons
        self._element_id = element_id
        self._process = process
        self._proxy_key = proxy_key
        # setup Qt signals and slots from the actions dictionary
        for b in self._buttons:
            b.clicked.connect(lambda: self._exec_action('clicked'))

    def _get_parameter(self):
        for i in range(len(self._choices)):
            if self._buttons[i].isChecked():
                return self._choices[i]

    def _set_parameter(self, value):
        with self._block_signals():
            for i in range(len(self._choices)):
                if value == self._choices[i]:
                    self._buttons[i].setChecked(True)
                else:
                    self._buttons[i].setChecked(False)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_value(self):
        return self._get_parameter()

    def _set_value(self, value):
        self._set_parameter(value)

    value = property(_get_value, _set_value, doc=\
        """The value selected by the user.""")


#
# ScrollBar
#
class ScrollBar(pythics.libcontrol.Control):
    """A free-standing scroll bar which is useful for easily changing a value.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *tracking*: [ *True* | *False* (default) ]
        whether to emit many 'valueChanged' events as the scrollbar is dragged

      *orientation*: [ 'horizontal' (default) | 'vertical' ]
        orientation of the scrollbar

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        =================    ==================================================
        signal               when emitted
        =================    ==================================================
        'valueChanged'       scrollbar value changed
        'actionTriggered'
        'rangeChanged'
        'sliderMoved'
        'sliderPressed'
        'sliderReleased'
        =================    ==================================================
    """
    def __init__(self, parent, tracking=False, orientation='horizontal',
                 **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        if orientation != 'horizontal':
            self._style = QtCore.Qt.Vertical
        else:
            self._style = QtCore.Qt.Horizontal
        self._widget = QtWidgets.QScrollBar(self._style)
        self._widget.setTracking(tracking)

    def _get_parameter(self):
        return (self._widget.value(), self._widget.pageStep(),
                self._widget.maximum())

    def _set_parameter(self, value):
        with self._block_signals():
            self._widget.setMaximum(value[2])
            self._widget.setPageStep(value[1])
            self._widget.setValue(value[0])

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_value(self):
        return self._widget.value()

    def _set_value(self, value):
        with self._block_signals():
            self._widget.setValue(value)

    value = property(_get_value, _set_value, doc=\
        """An integer giving the current scroll bar position.""")
        
    def _get_ranges(self):
        return (self._widget.pageStep(), self._widget.maximum())

    def _set_ranges(self, value):
        self._widget.setMaximum(value[1])
        self._widget.setPageStep(value[0])

    ranges = property(_get_ranges, _set_ranges, doc=\
        """A tuple containing the maximum scroll value and page step.""")


#
# Shell: Python console
#
class Shell(pythics.libcontrol.Control):
    """A Python shell which runs in the backend process for testing and
    debugging. You must set `initialization_action` to be a function which calls
    the interact() method of the Shell object to start it and to set the
    accesible objects.

    HTML parameters:

      *font*: str (default 'Consolas')
        name of font to use for shell text

      *font_size*: int (default 10)
        size of font to use for shell text in points

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'initialized'       startup
        ================    ===================================================
    """
    def __init__(self, parent, font='Consolas', font_size=10, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = pythics.control_helpers.Shell(self._push, font=font, font_size=font_size)

    def _register(self, process, element_id, proxy_key):
        self._element_id = element_id
        self._process = process
        if 'initialized' in self.actions:
            self._process.append_initialization_command(self.actions['initialized'])
        self._queue = self._process.manager.Queue()
        self._proxy = pythics.proxies.ShellProxy(self._queue, proxy_key)

    def _push(self, data):
        self._queue.put(data)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def write(self, text):
        self._widget.appendPlainText(text)

    def write_new_prompt(self):
        self._widget.newPrompt()

    def write_continue_prompt(self):
        self._widget.continuePrompt()

    def message(self, message):
        self._widget.appendPlainText(message)
        self._widget.newPrompt()


##
## Slider: sliding control (integer only)
##
#class Slider(pythics.libcontrol.Control):
#    """A scrollbar-like control for setting a numerical value.
#
#    HTML parameters:
#
#      *save*: [ *True* (default) | *False* ]
#        whether to save the value as a default
#
#      *tracking*: [ *True* | *False* (default) ]
#
#      *minimum*: float (default 0)
#
#      *maximum*: float (default 100)
#
#      *step*: float (default 0.0)
#
#      *scale_step*: float (default 0.1)
#
#      *orientation*: [ 'horizontal' (default) | 'vertical' ]
#
#      *scale_position*: [ 'top' | 'bottom' | 'left' | 'right' | *None* (default) ]
#
#      *style*: [ 'trough' (default) | 'slot' | 'both' ]
#
#      *actions*: dict
#        a dictionary of key:value pairs where the key is the name of a signal
#        and value is the function to run when the signal is emitted
#
#        actions in this control:
#
#        ================    ===================================================
#        signal              when emitted
#        ================    ===================================================
#        'valueChanged'      value is changed
#        'sliderPressed'     user starts to drag the slider
#        'sliderMoved'       user drags the slider
#        'sliderReleased'    user releases the slider
#        ================    ===================================================
#    """
#    def __init__(self, parent, tracking=False,
#                    minimum=0, maximum=100, step=0.0, scale_step=0.1,
#                    orientation='horizontal', scale_position=None, style='trough',
#                 **kwargs):
#        #signals = ['valueChanged']
#        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
#        # orientation selection
#        if orientation == 'horizontal':
#            orient = QtCore.Qt.Horizontal
#        else:
#            orient = QtCore.Qt.Vertical
##        # scale position selection
##        if scale_position == 'top':
##            scalePos = Qwt.QwtSlider.TopScale
##        elif scale_position == 'bottom':
##            scalePos = Qwt.QwtSlider.BottomScale
##        elif scale_position == 'left':
##            scalePos = Qwt.QwtSlider.LeftScale
##        elif scale_position == 'right':
##            scalePos = Qwt.QwtSlider.RightScale
##        else:
##            scalePos = Qwt.QwtSlider.NoScale
##        # background style selection
##        if style == 'trough':
##            bgStyle = Qwt.QwtSlider.BgTrough
##        elif style == 'slot':
##            bgStyle = Qwt.QwtSlider.BgSlot
##        else:
##            bgStyle = Qwt.QwtSlider.BgTrough | Qwt.QwtSlider.BgSlot
#        self._widget = QtGui.QSlider(orient)
#        self._widget.setTracking(tracking)
#        self._widget.setMinimum(int(minimum))
#        self._widget.setMaximum(int(maximum))
#        self._widget.setRange(float(minimum), float(maximum), float(step))
#
#    def get_parameter(self):
#        return self._widget.value()
#
#    def set_parameter(self, value):
#        with self._block_signals():
#            self._widget.fitValue(value)
#
#    #---------------------------------------------------
#    # methods below used only for access by action proxy
#
#    def _get_value(self):
#        return self._widget.value()
#
#    def _set_value(self, value):
#        with self._block_signals():
#            self._widget.fitValue(value)
#
#    value = property(_get_value, _set_value)


#
# SubWindow
#
class SubWindow(pythics.libcontrol.Control):
    """A box which can contain a collection of widgets specified in an html file.

    HTML parameters:

      *filename*: str (default '')
        name of html filename containing widget layout to display
    """
    def __init__(self, parent, filename='', **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = pythics.html.HtmlWindow(parent, 'pythics.controls')
        anonymous_controls, controls = self._widget.open_file(filename)
        # dictionary of controls (widgets)
        self._controls = controls
        # list of controls without ids
        self._anonymous_controls = anonymous_controls

    def _register(self, process, element_id, proxy_key):
        self._element_id = element_id
        self._process = process
        self._proxy_key = proxy_key
        self._proxy = pythics.proxies.SubWindowProxy()
        for k, v in self._controls.items():
            # _register() controls in the SubWindow
            pk = process.new_ProxyKey(v)
            if hasattr(v, '_register'):
                v._register(process, k, pk)
            # update control_proxies
            if hasattr(v, '_proxy'):
                # use a custom proxy
                self._proxy[k] = v._proxy
            else:
                # use a standard AutoProxy
                self._proxy[k] = pythics.libproxy.AutoProxy(pk, enable_cache=True)
        for v in self._anonymous_controls:
            if hasattr(v, '_register'):
                v._register(process, None, None)

    #--------------------------
    # the usual Control methods

    def _redraw(self):
        for k, c in list(self._controls.items()):
            c._redraw()

    def _get_parameter(self):
        # gather data from each control in the SubWindow in a dict
        #   the SubWindow itself has no data
        data_dict = dict()
        for k, control in self._controls.items():
            if control.save == True:
                data_dict[k] = control._get_parameter()
        return data_dict

    def _set_parameter(self, value):
        # set data in each control in the SubWindow
        #   the SubWindow itself has no data
        for k, data in value.items():
            try:
                self._controls[k]._set_parameter(data)
            except KeyError:
                pythics.logging.report_warning("id '%s' in parameter file has no corresponding control." % k)


#
# TextBox: text entry box
#
class TextBox(pythics.libcontrol.Control):
    """A widget for entering and displaying text data.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *align*: [ 'left' (default) | 'center' | 'right' ]
        justification of text

      *multiline*: [ *True* | *False* (default) ]
        whether there are multiple lines of text to display

      *read_only*: [ *True* | *False* (default) ]
        if *True*, the text cannot be edited by the user

      *font*: str (default 'Consolas')
        name of font to use for text

      *font_size*: int (default 10)
        size of font to use for text in points

      *font_weight*: ['Light' | 'Normal' (default) | 'DemiBold' | 'Bold' | 'Black']

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        =======================    ============================================
        signal                     when emitted
        =======================    ============================================
        'textChanged'              text is changed
        'copyAvailable'
        'cursorPositionChanged'
        'redoAvailable'
        'selectionChanged'
        'undoAvailable'
         =======================    ============================================
    """
    def __init__(self, parent, align='left', multiline=False, read_only=False,
                 font='Consolas', font_size=10, font_weight='Normal', **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = QtWidgets.QTextEdit()
        if read_only:
            self._widget.setReadOnly(True)
        if align == 'right':
            self._alignment = QtCore.Qt.AlignRight
        elif align == 'center':
            self._alignment = QtCore.Qt.AlignCenter
        else:
            self._alignment = QtCore.Qt.AlignLeft
        self._widget.setAlignment(self._alignment)
        if multiline:
            self._widget.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        else:
            self._widget.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
            self._widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self._widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        if font_weight == 'Light':
            weight = QtGui.QFont.Light
        elif font_weight == 'DemiBold':
            weight = QtGui.QFont.DemiBold
        elif font_weight == 'Bold':
            weight = QtGui.QFont.Bold
        elif font_weight == 'Black':
            weight = QtGui.QFont.Black
        else:
            weight = QtGui.QFont.Normal
        self._widget.document().setDefaultFont(QtGui.QFont(font, font_size, weight))
        # set default height to approximately 1 line of text
        metrics = self._widget.fontMetrics()
        self._widget.setFixedHeight(1.8*metrics.lineSpacing())

    def _get_parameter(self):
        return self._widget.toPlainText()

    def _set_parameter(self, value):
        with self._block_signals():
            if type(value) == str:
                self._widget.setPlainText(value)
            else:
                self._widget.setPlainText(str(value))
            self._widget.setAlignment(self._alignment)

    #---------------------------------------
    # methods below used for access by proxy

    def _get_value(self):
        return self._get_parameter()

    def _set_value(self, value):
        self._set_parameter(value)

    value = property(_get_value, _set_value)

    def scroll(self, dx, dy):
        return self._widget.scrollContentsBy(dx, dy)


#
# TextIOBox: text entry box with file-like interface
#
class TextIOBox(TextBox):
    """A box for displaying text data with a file-like interface.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *align*: [ 'left' (default) | 'center' | 'right' ]
        justification of text

      *logging*: [ *True* | *False* (default) ]
        if *True*, optimize the display for speed of displaying the output of
        a Python logger

      *auto_update*: [ *True* (default) | *False* ]
        if *False*, a call to TextIOBox.flush() is required to display text;
        has no effect if *logging* is *True*

      *reverse*: [ *True* | *False* (default) ]
        if *True*, newer lines are displayed at the top;
        has no effect if *logging* is *True*

      *font*: str (default 'Consolas')
        name of font to use for text

      *font_size*: int (default 10)
        size of font to use for text in points
    """
    def __init__(self, parent, align='left', logging='False', auto_update=True,
                 reverse=False, font='Consolas', font_size=10,
                 **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = QtWidgets.QTextEdit()
        self._widget.setReadOnly(True)
        if align == 'right':
            self._widget.setAlignment(QtCore.Qt.AlignRight)
        elif align == 'center':
            self._widget.setAlignment(QtCore.Qt.AlignCenter)
        else:
            self._widget.setAlignment(QtCore.Qt.AlignLeft)
        self._widget.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self._widget.document().setDefaultFont(QtGui.QFont(font, font_size, QtGui.QFont.Normal))
        self._string_io = StringIO.StringIO()
        # if only write() flush(), and clear() are used, text can be simply appended
        #   for much greater speed, especially useful with logging
        self._logging = logging
        if logging:
            self._auto_update = False
            self._reverse = False
        else:
            self._auto_update = auto_update
            self._reverse = reverse

    def _get_parameter(self):
        return self._string_io.getvalue()

    def _set_parameter(self, value):
        self._string_io = StringIO.StringIO()
        self._string_io.write(value)
        self._update_value()

    def _update_value(self):
        s = self._string_io.getvalue()
        if self._reverse:
            sl = s.splitlines()
            sl.reverse()
            s = '\n'.join(sl)
        with self._block_signals():
            self._widget.setPlainText(s)
        if not self._reverse:
            # scroll to bottom
            sb = self._widget.verticalScrollBar()
            sb.setValue(sb.maximum())

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def clear(self, *args, **kwargs):
        self._string_io = StringIO.StringIO()
        if(self._auto_update or self._logging):
            self._update_value()

    def scroll(self, dx, dy):
        return self._widget.scrollContentsBy(dx, dy)

    def __iter__(self, *args, **kwargs):
        return self._string_io.__iter__(*args, **kwargs)

    def close(self, *args, **kwargs):
        pass

    def flush(self, *args, **kwargs):
        if not self._logging:
            result = self._string_io.flush(*args, **kwargs)
            self._update_value()
            return result

    def getvalue(self, *args, **kwargs):
        return self._string_io.getvalue(*args, **kwargs)

    def isatty(self, *args, **kwargs):
        return self._string_io.isatty(*args, **kwargs)

    def next(self, *args, **kwargs):
        return self._string_io.next(*args, **kwargs)

    def read(self, *args, **kwargs):
        return self._string_io.read(*args, **kwargs)

    def readline(self, *args, **kwargs):
        return self._string_io.readline(*args, **kwargs)

    def readlines(self, *args, **kwargs):
        return self._string_io.readlines(*args, **kwargs)

    def reset(self, *args, **kwargs):
        return self._string_io.reset(*args, **kwargs)
        if(self._auto_update or self._logging):
            self._update_value()

    def seek(self, *args, **kwargs):
        return self._string_io.seek(*args, **kwargs)

    def tell(self, *args, **kwargs):
        return self._string_io.tell(*args, **kwargs)

    def truncate(self, *args, **kwargs):
        self._string_io.truncate(*args, **kwargs)
        if(self._auto_update or self._logging):
            self._update_value()

    def write(self, *args, **kwargs):
        if self._logging:
            # accelerated writing for simple access
            # append() adds a newline so we remove the original newline
            # remove any blank lines, which were likely just newlines
            s = args[0].strip()
            if s != '':
                self._widget.append(s)
        elif(self._auto_update):
            self._update_value()

    def writelines(self, *args, **kwargs):
        self._string_io.writelines(*args, **kwargs)
        if(self._auto_update or self._logging):
            self._update_value()

    def __len__(self):
        return len(self._string_io.getvalue().splitlines())


#
# RunButton
#
class RunButton(pythics.libcontrol.Control):
    """A toggle button which makes calls to a specially-constructed function,
    the action for the `run` signal, to create an action at regular intervals.
    The run function should use the python yield keyword, followed by the
    desired delay or interval between calls, in seconds. The required delay
    will occur at the yield call, and during that delay other functions in your
    python file can be called. Thus, the runbutton gives the functionality of
    using a Timer with the simplicity of writing a loop. See the ChartRecorder
    example for a demonstration.

    In most cases, the RunButton will be started by pressing the button in the
    GUI, and ended by your run function returning, rather than yielding.
    Pressing the button to stop will abort and delay and allow your run
    function to return. From the python side, start(), stop(), abort(), and
    kill() give control over the execution, if needed.

    HTML parameters:

      *label*: str (default 'Start/Stop')
        text to be displayed on the button

      *interval*: [ *True* (default) | *False* ]
        whether the time given in the yield statement should be treated as a
        strict delay (interval=False) or as the requested time between steps in
        your run function (interval=True)

      *actions*: dict
        a dictionary of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'run'               button changes state from unpressed to pressed
        ================    ===================================================
    """
    def __init__(self, parent, label='Start/Stop', interval=True, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, save=False, **kwargs)
        self._widget = QtWidgets.QToolButton()
        self._widget.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self._widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                  QtWidgets.QSizePolicy.Fixed)
        self._widget.setText(label)
        self._widget.setCheckable(True)
        self._time_interval = interval

    def _register(self, process, element_id, proxy_key):
        self._element_id = element_id
        self._process = process
        if 'run' in self.actions:
            action = self.actions['run']
        else:
            action = None
        self._proxy = pythics.proxies.RunButtonProxy(self._element_id, action,
                                                     self._time_interval,
                                                     proxy_key)
        self._widget.toggled.connect(self._toggled)

    def _get_parameter(self):
        return self._widget.isChecked()

    def _set_parameter(self, value):
        with self._block_signals():
            self._widget.setChecked(value)

    def _toggled(self):
        if not self._blocked:
            if self._widget.isChecked():
                self._process.exec_parent_to_proxy_call_request(self._element_id,
                'start', update_button_state=False)
            else:
                self._process.exec_parent_to_proxy_call_request(self._element_id,
                'abort')

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_label(self):
        return self._widget.text()

    def _set_label(self, value):
        self._widget.setText(value)

    label = property(_get_label, _set_label, doc=\
        """Text to be displayed on the button.""")

    def _get_value(self):
        return self._widget.isChecked()

    def _set_value(self, value):
        with self._block_signals():
            self._widget.setChecked(value)

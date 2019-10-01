# -*- coding: utf-8 -*-
#
#  Copyright 2008 - 2019 Brian R. D'Urso
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
import time

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


class ImageLabel(QtWidgets.QWidget):
    def __init__(self, control, *args):
        QtWidgets.QWidget.__init__(self, *args)
        self.control = control
        self.image = None
        self.draw_w = 1
        self.draw_h = 1
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setSizePolicy(size_policy)

    def setScale(self, scale):
        self.scale = scale
        if self.image is not None:
            self.draw_w = self.scale*self.image_w
            self.draw_h = self.scale*self.image_h
            if not self.fit:
                self.setMinimumSize(self.draw_w, self.draw_h)
            self.repaint()

    def setFit(self, fit):
        self.fit = fit
        if fit:
            self.setMinimumSize(1, 1)
        else:
            self.setMinimumSize(self.draw_w, self.draw_h)
        self.repaint()

    def setImage(self, image):
        self.image = image
        self.image_w = image.width()
        self.image_h = image.height()
        self.draw_w = self.scale*self.image_w
        self.draw_h = self.scale*self.image_h
        if self.fit:
            self.setMinimumSize(1,1)
        else:
            self.setMinimumSize(self.draw_w, self.draw_h)
        self.repaint()

    def paintEvent(self, event):
        if self.image is not None:
            painter = QtGui.QPainter(self)
            if self.fit:
                scale = min(self.width()/float(self.image_w),
                            self.height()/float(self.image_h))
                x_offset = max(int((self.width()-self.image_w*scale)/2.0), 0)
                y_offset = max(int((self.height()-self.image_h*scale)/2.0), 0)
            else:
                x_offset = max(int((self.width()-self.draw_w)/2.0), 0)
                y_offset = max(int((self.height()-self.draw_h)/2.0), 0)
                scale = self.scale
            painter.save()
            painter.translate(x_offset, y_offset)
            painter.scale(scale, scale)
            painter.drawImage(0, 0, self.image)
            painter.restore()
            self.scale = scale
            self.x_offset = x_offset
            self.y_offset = y_offset

    def mousePressEvent(self, event):
        x = int((event.x()-self.x_offset)/float(self.scale))
        y = int((event.y()-self.y_offset)/float(self.scale))
        if event.button() == QtCore.Qt.LeftButton:
            self.control._mouse_press_left(x, y)
        elif event.button() == QtCore.Qt.RightButton:
            self.control._mouse_press_right(x, y)
        else:
            # pass on other buttons to base class
            QtWidgets.QWidget.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        x = int((event.x()-self.x_offset)/float(self.scale))
        y = int((event.y()-self.y_offset)/float(self.scale))
        if event.button() == QtCore.Qt.LeftButton:
            self.control._mouse_release_left(x, y)
        elif event.button() == QtCore.Qt.RightButton:
            self.control._mouse_release_right(x, y)
        else:
            # pass on other buttons to base class
            QtWidgets.QWidget.mouseReleaseEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        x = int((event.x()-self.x_offset)/float(self.scale))
        y = int((event.y()-self.y_offset)/float(self.scale))
        if event.button() == QtCore.Qt.LeftButton:
            self.control._mouse_double_click_left(x, y)
        elif event.button() == QtCore.Qt.RightButton:
            self.control._mouse_double_click_right(x, y)
        else:
            # pass on other buttons to base class
            QtWidgets.QWidget.mouseDoubleClickEvent(self, event)


#
# multiturn rotatable control to select a value from a set of choices
#
class Knob(QtWidgets.QDial):
    choiceChanged = Signal(int)    
    
    def __init__(self, steps=50, choices=['None'], acceleration=5.0, tracking=False, wrapping=False, prefix='', suffix=''):
        QtWidgets.QDial.__init__(self)
        self.setNotchesVisible(True)
        self.setStyle(QtWidgets.QStyleFactory.create('plastique'))
        self.steps = steps
        self.choices = choices
        self.choice_tracking = tracking
        self.index_wrapping = wrapping
        self.setWrapping(True)
        self.setTracking(True)
        self.last_position = 0
        self.last_index = 0
        self.setRange(0, self.steps)
        self.last_time = time.time()
        self.acceleration = acceleration
        self.prefix = prefix
        self.suffix = suffix
            
    def sliderChange(self, change):
        if change == 3: # QtWidgets.QAbstractSlider.SliderChange
            new_position = self.value()
            new_time = time.time()
            ccw_change = (self.last_position - new_position) % self.steps
            cw_change = (new_position - self.last_position) % self.steps
            if ccw_change < cw_change:
                # knob was turned CCW
                accel = int(ccw_change*self.acceleration/((abs(new_time-self.last_time)+0.001)*self.steps))
                if self.index_wrapping:
                     new_index = (self.last_index - ccw_change - accel) % len(self.choices)
                else:
                     new_index = max(0, self.last_index - ccw_change - accel)
            else:
                # knob was turned CW
                accel = int(cw_change*self.acceleration/((abs(new_time-self.last_time)+0.001)*self.steps))
                if self.index_wrapping:
                    new_index = (self.last_index + cw_change + accel) % len(self.choices)
                else:
                    new_index = min(len(self.choices)-1, self.last_index + cw_change + accel)
            self.last_position = new_position
            if new_index != self.last_index:
                self.last_index =  new_index
                if self.choice_tracking:
                    self.choiceChanged.emit(self.getChoiceValue())
            self.last_time = new_time
        QtWidgets.QDial.sliderChange(self, change)
        
    def mouseReleaseEvent(self, event):
        if not self.choice_tracking:
            self.choiceChanged.emit(self.getChoiceValue())
        QtWidgets.QDial.mouseReleaseEvent(self, event)
        
    def keyPressEvent(self, event):
        if not self.choice_tracking:
            self.choiceChanged.emit(self.getChoiceValue())
        QtWidgets.QDial.keyPressEvent(self, event)

    def wheelEvent(self, event):
        if not self.choice_tracking:
            self.choiceChanged.emit(self.getChoiceValue())
        QtWidgets.QDial.wheelEvent(self, event)

    def setChoices(self, choices):
        self.choices = choices

    def getChoices(self):
        return self.choices

    def setChoiceValue(self, value):
        self.last_index = self.choices.index(value)
        # request repaint
        self.update()

    def getChoiceValue(self):
        return self.choices[self.last_index]
        
    def paintEvent(self,event):
        QtWidgets.QDial.paintEvent(self,event)
        painter = QtGui.QPainter(self)      
        painter.setPen(QtGui.QPen(self.palette().color(QtGui.QPalette.Text), 1))
        painter.drawText(self.rect(), QtCore.Qt.AlignCenter, self.prefix+str(self.getChoiceValue())+self.suffix);
        

#
# floating point NumBox control
#
class ScientificDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, parent=None, format_str='%g', *args, **kwargs):
        QtWidgets.QDoubleSpinBox.__init__(self, parent, *args, **kwargs)
        self.format_str = format_str
        self.validator = QtGui.QDoubleValidator()

    def textFromValue(self, value):
        return self.format_str % value

    def validate(self, text, pos):
        return self.validator.validate(text, pos)

    def valueFromText(self, text):
        return float(text)

#
# floating point NumBox control with metric units
#
class MetricDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, parent=None, format_str='%g', base_unit='', metric_prefix='', *args, **kwargs):
        self.format_str = format_str
        self.base_unit = base_unit
        self.metric_prefix_value = self.lookup_metric_prefix_value(metric_prefix)
        suffix = ' ' + metric_prefix + base_unit
        self.set_unit(suffix)
        self.validator = QtGui.QDoubleValidator()
        QtWidgets.QDoubleSpinBox.__init__(self, parent, *args, **kwargs)
        self.setSuffix(suffix)
        # create the context menu
        self.context_menu = QtWidgets.QMenu()
        self.context_menu_action_group = QtWidgets.QActionGroup(self, exclusive=True)
        # add menu items
        self.action_yotta = self.add_prefix_to_context_menu('Y (yotta)')
        self.action_zetta = self.add_prefix_to_context_menu('Z (zetta)')
        self.action_exa = self.add_prefix_to_context_menu('E (exa)')
        self.action_peta = self.add_prefix_to_context_menu('P (peta)')
        self.action_tera = self.add_prefix_to_context_menu('T (tera)')
        self.action_giga = self.add_prefix_to_context_menu('G (giga)')
        self.action_mega = self.add_prefix_to_context_menu('M (mega)')
        self.action_kilo = self.add_prefix_to_context_menu('k (kilo)')
        self.action_hecto = self.add_prefix_to_context_menu('h (hecto)')
        self.action_deca = self.add_prefix_to_context_menu('da (deca)')
        self.action_none = self.add_prefix_to_context_menu('(none)')
        self.action_deci = self.add_prefix_to_context_menu('d (deci)')
        self.action_centi = self.add_prefix_to_context_menu('c (centi)')
        self.action_milli = self.add_prefix_to_context_menu('m (milli)')
        self.action_micro = self.add_prefix_to_context_menu('\u03bc (micro)')
        self.action_nano = self.add_prefix_to_context_menu('n (nano)')
        self.action_pico = self.add_prefix_to_context_menu('p (pico)')
        self.action_femto = self.add_prefix_to_context_menu('f (femto)')
        self.action_atto = self.add_prefix_to_context_menu('a (atto)')
        self.action_zepto = self.add_prefix_to_context_menu('z (zepto)')
        self.action_yocto = self.add_prefix_to_context_menu('y (yocto)')
        # set initially checked item
        if metric_prefix == 'y':
            self.action_yocto.setChecked(True)
        elif metric_prefix == 'z':
            self.action_zepto.setChecked(True)
        elif metric_prefix == 'a':
            self.action_atto.setChecked(True)
        elif metric_prefix == 'f':
            self.action_femto.setChecked(True)
        elif metric_prefix == 'p':
            self.action_pico.setChecked(True)
        elif metric_prefix == 'n':
            self.action_nano.setChecked(True)
        elif metric_prefix == '\u03bc' or metric_prefix == 'u':
            self.action_micro.setChecked(True)
        elif metric_prefix == 'm':
            self.action_milli.setChecked(True)
        elif metric_prefix == 'c':
            self.action_centi.setChecked(True)
        elif metric_prefix == 'd ':
            self.action_deci.setChecked(True)
        elif metric_prefix == 'da':
            self.action_deca.setChecked(True)
        elif metric_prefix == 'h':
            self.action_hecto.setChecked(True)
        elif metric_prefix == 'k':
            self.action_kilo.setChecked(True)
        elif metric_prefix == 'M':
            self.action_mega.setChecked(True)
        elif metric_prefix == 'G':
            self.action_giga.setChecked(True)
        elif metric_prefix == 'T':
            self.action_tera.setChecked(True)
        elif metric_prefix == 'P':
            self.action_peta.setChecked(True)
        elif metric_prefix == 'E':
            self.action_exa.setChecked(True)
        elif metric_prefix == 'Z':
            self.action_zetta.setChecked(True)
        elif metric_prefix == 'Y':
            self.action_yotta.setChecked(True)
        else:
            self.action_none.setChecked(True)
        # connect the context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)
        
    def set_unit(self, unit):
        self.unit = unit
        self.unit_length = len(unit)

    def valueFromText(self, text):
        num_text = text.split(' ')[0]
        return float(num_text)*self.metric_prefix_value
                
    def textFromValue(self, value):
        return (self.format_str % (value/self.metric_prefix_value))

    def validate(self, text, pos):
        if text[-self.unit_length:] == self.unit:
            result = self.validator.validate(text[:-self.unit_length], pos)
            return (result[0], text, result[2])
        else:
            return self.validator.validate(text, pos)

    def add_prefix_to_context_menu(self, s):
        if s == '(none)':
            prefix = ''
        elif s == 'da (deca)':
            prefix = 'da'
        else:
            prefix = s[:1]
        action = QtWidgets.QAction(s, self, checkable=True,
                               triggered=(lambda: self.on_change_metric_prefix(prefix)))
        self.context_menu_action_group.addAction(action)
        self.context_menu.addAction(action)
        return action

    def on_context_menu(self, point):
        self.context_menu.exec_(self.mapToGlobal(point))
        
    def lookup_metric_prefix_value(self, prefix):
        if prefix[:1] == 'y':
            return 1e-24
        elif prefix[:1] == 'z':
            return 1e-21
        elif prefix[:1] == 'a':
            return 1e-18
        elif prefix[:1] == 'f':
            return 1e-15
        elif prefix[:1] == 'p':
            return 1e-12
        elif prefix[:1] == 'n':
            return 1e-9
        elif prefix[:1] == '\u03bc' or prefix[:1] == 'u':
            return 1e-6
        elif prefix[:1] == 'm':
            return 1e-3
        elif prefix[:1] == 'c':
            return 1e-2
        elif prefix[:2] == 'd ' or prefix[:2] == 'd':
            return 1e-1
        elif prefix[:2] == 'da':
            return 1e1
        elif prefix[:1] == 'c':
            return 1e2
        elif prefix[:1] == 'k':
            return 1e3
        elif prefix[:1] == 'M':
            return 1e6
        elif prefix[:1] == 'G':
            return 1e9
        elif prefix[:1] == 'T':
            return 1e12
        elif prefix[:1] == 'P':
            return 1e15
        elif prefix[:1] == 'E':
            return 1e18
        elif prefix[:1] == 'Z':
            return 1e21
        elif prefix[:1] == 'Y':
            return 1e24
        else:
            return 1

    def on_change_metric_prefix(self, new_prefix):
        v = self.value()
        self.metric_prefix_value = self.lookup_metric_prefix_value(new_prefix)
        suffix = ' ' + new_prefix + self.base_unit
        self.setSuffix(suffix)
        self.set_unit(suffix)
        self.setValue(v)


#
# Python shell widget for Shell control
#
class Shell(QtWidgets.QPlainTextEdit):
    def __init__(self, push_func, prompt='$> ', parent=None, font='Consolas', font_size=10, *args, **kwargs):
        QtWidgets.QPlainTextEdit.__init__(self, parent, *args, **kwargs)
        self.prompt = prompt
        self.history = []
        self.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)
        self.setUndoRedoEnabled(False)
        self.document().setDefaultFont(QtGui.QFont(font, font_size, QtGui.QFont.Normal))
        self.push = push_func

    def newPrompt(self):
        self.appendPlainText(self.prompt)
        self.moveCursor(QtGui.QTextCursor.End)

    def continuePrompt(self):
        self.appendPlainText('.' * len(self.prompt))
        self.moveCursor(QtGui.QTextCursor.End)

    def getCommand(self):
        doc = self.document()
        curr_line = str(doc.findBlockByLineNumber(doc.lineCount() - 1).text())
        curr_line = curr_line.rstrip()
        curr_line = curr_line[len(self.prompt):]
        return curr_line

    def setCommand(self, command):
        if self.getCommand() == command:
            return
        self.moveCursor(QtGui.QTextCursor.End)
        self.moveCursor(QtGui.QTextCursor.StartOfLine, QtGui.QTextCursor.KeepAnchor)
        for i in range(len(self.prompt)):
            self.moveCursor(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)
        self.textCursor().removeSelectedText()
        self.textCursor().insertText(command)
        self.moveCursor(QtGui.QTextCursor.End)

    def addToHistory(self, command):
        if command and (not self.history or self.history[-1] != command):
            self.history.append(command)
        self.history_index = len(self.history)

    def getPrevHistoryEntry(self):
        if self.history:
            self.history_index = max(0, self.history_index - 1)
            return self.history[self.history_index]
        return ''

    def getNextHistoryEntry(self):
        if self.history:
            hist_len = len(self.history)
            self.history_index = min(hist_len, self.history_index + 1)
            if self.history_index < hist_len:
                return self.history[self.history_index]
        return ''

    def getCursorPosition(self):
        return self.textCursor().columnNumber() - len(self.prompt)

    def setCursorPosition(self, position):
        self.moveCursor(QtGui.QTextCursor.StartOfLine)
        for i in range(len(self.prompt) + position):
            self.moveCursor(QtGui.QTextCursor.Right)

    def runCommand(self):
        command = self.getCommand()
        self.addToHistory(command)
        self.push(command)

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            self.runCommand()
            return
        if event.key() == QtCore.Qt.Key_Home:
            self.setCursorPosition(0)
            return
        if event.key() == QtCore.Qt.Key_PageUp:
            return
        elif event.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Backspace):
            if self.getCursorPosition() == 0:
                return
        elif event.key() == QtCore.Qt.Key_Up:
            self.setCommand(self.getPrevHistoryEntry())
            return
        elif event.key() == QtCore.Qt.Key_Down:
            self.setCommand(self.getNextHistoryEntry())
            return
        elif event.key() == QtCore.Qt.Key_D and event.modifiers() == QtCore.Qt.ControlModifier:
            self.close()
        super(Shell, self).keyPressEvent(event)

# -*- coding: utf-8 -*-
#
#  Copyright 2008 - 2014 Brian R. D'Urso
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

#from PyQt4 import QtCore, QtGui
from pythics.settings import _TRY_PYSIDE
try:
    if not _TRY_PYSIDE:
        raise ImportError()
    import PySide.QtCore as _QtCore
    import PySide.QtGui as _QtGui
    QtCore = _QtCore
    QtGui = _QtGui
    Signal = QtCore.Signal
    USES_PYSIDE = True
except ImportError:
    import sip
    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)
    import PyQt4.QtCore as _QtCore
    import PyQt4.QtGui as _QtGui
    QtCore = _QtCore
    QtGui = _QtGui
    Signal = QtCore.pyqtSignal
    USES_PYSIDE = False


class ImageLabel(QtGui.QWidget):
    def __init__(self, control, *args):
        QtGui.QWidget.__init__(self, *args)
        self.control = control
        self.image = None
        self.draw_w = 1
        self.draw_h = 1
        size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
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
            QtGui.QWidget.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        x = int((event.x()-self.x_offset)/float(self.scale))
        y = int((event.y()-self.y_offset)/float(self.scale))
        if event.button() == QtCore.Qt.LeftButton:
            self.control._mouse_release_left(x, y)
        elif event.button() == QtCore.Qt.RightButton:
            self.control._mouse_release_right(x, y)
        else:
            # pass on other buttons to base class
            QtGui.QWidget.mouseReleaseEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        x = int((event.x()-self.x_offset)/float(self.scale))
        y = int((event.y()-self.y_offset)/float(self.scale))
        if event.button() == QtCore.Qt.LeftButton:
            self.control._mouse_double_click_left(x, y)
        elif event.button() == QtCore.Qt.RightButton:
            self.control._mouse_double_click_right(x, y)
        else:
            # pass on other buttons to base class
            QtGui.QWidget.mouseDoubleClickEvent(self, event)


#
# multiturn rotatable control to select a value from a set of choices
#
class Knob(QtGui.QDial):
    choiceChanged = Signal(int)    
    
    def __init__(self, steps=50, choices=['None'], acceleration=5.0, tracking=False, wrapping=False):
        QtGui.QDial.__init__(self)
        self.setNotchesVisible(True)
        self.setStyle(QtGui.QStyleFactory.create('plastique'))
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
            
    def sliderChange(self, change):
        if change == 3: # QtGui.QAbstractSlider.SliderChange
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
        QtGui.QDial.sliderChange(self, change)
        
    def mouseReleaseEvent(self, event):
        if not self.choice_tracking:
            self.choiceChanged.emit(self.getChoiceValue())
        QtGui.QDial.mouseReleaseEvent(self, event)
        
    def keyPressEvent(self, event):
        if not self.choice_tracking:
            self.choiceChanged.emit(self.getChoiceValue())
        QtGui.QDial.keyPressEvent(self, event)

    def wheelEvent(self, event):
        if not self.choice_tracking:
            self.choiceChanged.emit(self.getChoiceValue())
        QtGui.QDial.wheelEvent(self, event)

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
        QtGui.QDial.paintEvent(self,event)
        painter = QtGui.QPainter(self)      
        painter.setPen(QtGui.QPen(self.palette().color(QtGui.QPalette.Text), 1))
        painter.drawText(self.rect(), QtCore.Qt.AlignCenter, str(self.getChoiceValue()));
        

#
# floating point NumBox control
#
class ScientificDoubleSpinBox(QtGui.QDoubleSpinBox):
    def __init__(self, parent=None, format_str='%g', *args, **kwargs):
        QtGui.QDoubleSpinBox.__init__(self, parent, *args, **kwargs)
        self.format_str = format_str
        self.validator = QtGui.QDoubleValidator()

    def textFromValue(self, value):
        return self.format_str % value

    def validate(self, text, pos):
        return self.validator.validate(text, pos)

    def valueFromText(self, text):
        return float(text)

#
# Python shell widget for Shell control
#
class Shell(QtGui.QPlainTextEdit):
    def __init__(self, push_func, prompt='$> ', parent=None, font='Consolas', font_size=10, *args, **kwargs):
        QtGui.QPlainTextEdit.__init__(self, parent, *args, **kwargs)
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
        curr_line = unicode(doc.findBlockByLineNumber(doc.lineCount() - 1).text())
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

# -*- coding: utf-8 -*-
#
# Originally in C++, released under GPL v2 or later at 
#   http://qt-apps.org/content/show.php/QScale?content=148053
# Ported to Python by Fabian Inostroza, 2014
# Modified by Brian R. D'Urso, 2014:
#  - fixed Pyside compatibility
#  - fixed vertical mode functionality
#  - changed needle color and shape
#  - added frame and changed default background color
#  - scattered cleanup
#  - now released under GPL v3 or later
#  - TODO: SetRange only works with integers! FIXED???
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

#from PyQt4 import QtGui, QtCore
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

import sys
from math import pi, isinf, sqrt, asin, ceil, cos, sin


class QMeter(QtGui.QFrame):
    def __init__(self,parent=None):
        super(QMeter,self).__init__(parent)
        self.setAutoFillBackground(True)
        self.setFrameStyle(QtGui.QFrame.Box)
        #self.setFrameStyle(QtGui.QFrame.Box|QtGui.QFrame.Plain)
        self.setLineWidth(1)
        self.m_minimum = 0
        self.m_maximum = 100
        self.m_value = 0
        
        self.m_labelsVisible = True
        self.m_scaleVisible = True
        
        self.m_borderWidth = 6
        self.m_labelsFormat = 'f'
        self.m_labelsPrecision = 0#-1
        self.m_majorStepSize = 0
        self.m_minorStepCount = 0
        
        self.m_invertedAppearance = False
        self.m_orientations = QtCore.Qt.Horizontal | QtCore.Qt.Vertical
        
        self.setBackgroundRole(QtGui.QPalette.Base)
        
        self.labelSample = ""
        self.updateLabelSample()
        self.setMinimumSize(80,60)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        
    # THIS LOOKS WRONG!!!
    def setMinimum(self, max_in):
        if not isinf(max_in):
            self.m_maximum = max_in
        self.updateLabelSample()
        self.update()
        
    def maximum(self):
        return self.m_maximum
        
    def setRange(self, min_in, max_in):
        if not isinf(min_in):
            self.m_minimum = min_in
        if not isinf(max_in):
            self.m_maximum = max_in
        self.updateLabelSample()
        self.update()
        
    def setValue(self, val):
        self.m_value = val
        self.update()
        
    def value(self):
        return self.m_value
    
    def setLabelsVisible(self, visible):
        self.m_labelsVisible = visible
        self.update()
        
    def isLabelsVisible(self):
        return self.m_labelsVisible
        
    def setScaleVisible(self,visible):
        self.m_scaleVisible = visible
        self.update()
        
    def isScaleVisible(self):
        return self.m_scaleVisible
        
    def setBorderWidth(self,width):
        self.m_borderWidth = width if width > 0 else 0
        self.update()
        
    def borderWidth(self):
        return self.m_borderWidth
        
    def setLabelsFormat(self, fmt, precision):
        self.m_labelsFormat = fmt
        self.m_labelsPrecision = precision
        self.updateLabelSample()
        self.update()
        
    def setMajorStepSize(self,stepsize):
        self.m_majorStepSize = stepsize
        self.update()
        
    def majorStepSize(self):
        return self.m_majorStepSize
        
    def setMinorStepSize(self,stepcount):
        self.m_minorStepCount = stepcount
        self.update()
        
    def minorStepCount(self):
        return self.m_minorStepCount
        
    def setInvertedAppearance(self,invert):
        self.m_invertedAppearance = invert
        self.update()
        
    def invertedAppearance(self):
        return self.m_invertedAppearance
        
    # orientations es Qt::Orientations
    def setOrientations(self,orientations):
        self.m_orientations = orientations
        self.update()
    
    def orientations(self):
        return self.m_orientations
        
    def resizeEvent(self,re):
        super(QMeter,self).resizeEvent(re)
        
    def paintEvent(self, paintEvent):
        # do custom painting
        painter = QtGui.QPainter(self)
        
        if (not (self.m_orientations & QtCore.Qt.Vertical)) ^ (not (self.m_orientations & QtCore.Qt.Horizontal)):
            vertical = self.m_orientations & QtCore.Qt.Vertical
        else:
            vertical = self.height() > self.width()
            
        painter.setRenderHint(QtGui.QPainter.Antialiasing,True)
        
        boundingRect = painter.boundingRect(QtCore.QRectF(0,0,self.width(),self.height()),
                                                 QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter,self.labelSample)
                                                 
        if vertical:
            hWidget = self.width()
            wWidget = self.height()
            hLabel = boundingRect.width() if self.m_labelsVisible else 0
            wLabel = boundingRect.height() if self.m_labelsVisible else 0
        else:
            wWidget = self.width()
            hWidget = self.height()
            wLabel = boundingRect.width() if self.m_labelsVisible else 0
            hLabel = boundingRect.height() if self.m_labelsVisible else 0
        
        wScale = wWidget - wLabel - 2.0*self.m_borderWidth
        
        hScale = 0.5*hWidget - hLabel - self.m_borderWidth
        
        radius = 0.125*wScale**2/hScale + 0.5*hScale
        
        if radius < hScale + 0.5*hWidget - self.m_borderWidth:
            radius = (4.0*(hLabel+self.m_borderWidth) + \
                        sqrt(4.0*(hLabel+self.m_borderWidth)**2 + 3.0*wScale**2))/3.0 - \
                        hLabel - 2.0*self.m_borderWidth
            center = QtCore.QPointF(0.5*wWidget,hWidget-self.m_borderWidth)
        else:
            center = QtCore.QPointF(0.5*wWidget,radius+hLabel+self.m_borderWidth)
            
        angleSpan = -360.0/pi*asin(wScale/(2.0*radius))
        angleStart = 90.0 - 0.5*angleSpan
        
        valueSpan = self.m_maximum - self.m_minimum
        majorStep = abs(valueSpan)*max(wLabel,1.5*boundingRect.height())/wScale
        order = 0
        
        while majorStep < 1:
            majorStep *= 10
            order -= 1
            
        while majorStep >= 10:
            majorStep /= 10
            order += 1
        
        if majorStep > 5:
            majorStep = 10*10**order
            minorSteps = 5
        elif majorStep > 2:
            majorStep = 5*10**order
            minorSteps = 5
        else:
            majorStep = 2*10**order
            minorSteps = 4
        
        if self.m_majorStepSize > 0:
            majorStep = self.m_majorStepSize
        if self.m_minorStepCount > 0:
            minorSteps = self.m_minorStepCount
            
        painter.setPen(QtGui.QPen(self.palette().color(QtGui.QPalette.Text),1))
        if self.m_scaleVisible and majorStep != 0:
            if vertical:
                painter.rotate(90)
                painter.translate(0,-hWidget+wLabel/4.0)
            
            painter.translate(center)

            painter.rotate(self.m_minimum%(float(majorStep)/float(minorSteps))/float(valueSpan)*angleSpan-angleStart)
            
            offsetCount = (minorSteps-ceil(self.m_minimum%majorStep)/float(majorStep)*minorSteps)%minorSteps
            
            scaleWidth = min(0.25*(hWidget-self.m_borderWidth),0.25*radius,2.5*boundingRect.height())
            
            for i in range(0, int(round(minorSteps*valueSpan/majorStep+1))):
                if i % minorSteps == offsetCount:
                    painter.drawLine(QtCore.QLineF(radius-scaleWidth,0,radius,0))
                else:
                    painter.drawLine(QtCore.QLineF(radius-scaleWidth,0,
                                                   radius-scaleWidth*0.4,0))
                                                   
                painter.rotate(majorStep*angleSpan/(-valueSpan*minorSteps))
                    
            painter.resetMatrix()
            
        # draw labels
        if self.m_labelsVisible and majorStep != 0:
            x= range(int(ceil(self.m_minimum/majorStep)), int(self.m_maximum/majorStep)+1)
            for i in x:
                u = pi/180.0*((majorStep*i-self.m_minimum)/float(valueSpan)*angleSpan+angleStart)
                position = QtCore.QRect()
                if vertical:
                    align = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
                    position = QtCore.QRect(self.width()-center.y()+radius*sin(u),0,
                                            self.width(),self.height()+2*radius*cos(u))
                else:
                    align = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom
                    position = QtCore.QRect(0,0,2.0*(center.x()+radius*cos(u)),
                                            center.y()-radius*sin(u))
                
                painter.resetMatrix()
                painter.drawText(position, align, self.m_labelsFormatter.format(float(i*majorStep)))
                                        
        # draw neddle
        if vertical:
            painter.rotate(90)
            painter.translate(0, -hWidget+wLabel/4.0)
        
        painter.translate(center)
        painter.rotate((self.m_minimum-self.m_value)/float(valueSpan)*angleSpan-angleStart)
        painter.setPen(QtCore.Qt.NoPen)
        #painter.setBrush(self.palette().color(QtGui.QPalette.Text))
        painter.setBrush(QtCore.Qt.red)
        self.polygon = QtGui.QPolygon()
        # easy way to set polygon is
        #self.polygon.setPoints(0,-2,int(radius)-scaleWidth,-2,int(radius)-scaleWidth/2,0,
        #                  int(radius)-scaleWidth,2,0,2)
        # but that doesn't work in PySide
        # instead, use
        self.polygon.append(QtCore.QPoint(0, -2))
        self.polygon.append(QtCore.QPoint(int(radius)-scaleWidth, -2))
        self.polygon.append(QtCore.QPoint(int(radius)-scaleWidth/2, 0))
        self.polygon.append(QtCore.QPoint(int(radius)-scaleWidth, 2))
        self.polygon.append(QtCore.QPoint(0, 2))

        painter.drawConvexPolygon(self.polygon)
        painter.resetMatrix()
        
        # draw cover
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(self.palette().color(QtGui.QPalette.Mid))
        
        if vertical:
            painter.drawRect(QtCore.QRect(0,0,self.m_borderWidth,self.height()))
            center = QtCore.QPoint(self.width()-center.y()-wLabel/4.0, 0.5*self.height())
            u = 0.25*(hWidget-wLabel)-center.x()-self.m_borderWidth
        else:
            pass
            painter.drawRect(QtCore.QRect(0,hWidget,wWidget, -self.m_borderWidth))
            u = center.y() - self.m_borderWidth - 0.75*hWidget
        
        u = max(u,0.25*radius)
        painter.drawEllipse(center, u, u)
        
        # pass paint event to base class to draw the frame border
        super(QMeter,self).paintEvent(paintEvent)

    def updateLabelSample(self):
        self.m_labelsFormatter = "{0:." + str(self.m_labelsPrecision) + self.m_labelsFormat + "}"
        margin = max(abs(self.m_minimum),abs(self.m_maximum))
        if min(self.m_minimum,self.m_maximum) < 0:
            wildcard = float(-8)
        else:
            wildcard = float(8)
        
        while margin < 1:
            margin *= 10
            wildcard /= 10
        
        while margin >= 10:
            margin /= 10
            wildcard *= 10
            
        self.labelSample = self.m_labelsFormatter.format(wildcard)

        
if __name__ == '__main__':
    global j
    j = 100
    def update():
        global j
        if j==0:
            j=100
        else:
            j -= 1
        scale.setValue(j)
        
    app = QtGui.QApplication(sys.argv)
    scale = QMeter()
    timer = QtCore.QTimer()
    timer.setInterval(100)
    timer.timeout.connect(update)
    timer.start()
    scale.show()
    sys.exit(app.exec_())

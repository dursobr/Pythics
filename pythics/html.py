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
import importlib
import re
import io
import sys, traceback

try:
    from lxml import etree as ElementTree
    lxml_loaded = True
except ImportError as e:
    sys.stderr.write("Error: failed to import lxml module ({})".format(e))
    from xml.etree import ElementTree
    lxml_loaded = False

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


class XMLError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Hyperlink(QtWidgets.QLabel):
    def __init__(self, parent, label, url):
        super(Hyperlink, self).__init__('<a href=#'+url+'>'+label+'</a>')
        self.setTextFormat(QtCore.Qt.RichText)
        self.parent = parent
        self.url = url
        self.linkActivated.connect(self.go_to_url)

    def go_to_url(self, url):
        self.parent.scroll_to_anchor(self.url)


default_style_sheet = """
    body {align: left; background-color: #eeeeee; margin: 10px; padding: 5px;
    color: black; font-size: 12pt; font-family: default; font-style: normal;
    font-weight: normal;}
"""


xmlschema_f = io.BytesIO(b'''\
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">

  <!-- definition of element groups -->
  <xs:group name="bodygroup">
    <xs:choice>
      <xs:element ref="a"/>
      <xs:element ref="br"/>
      <xs:element ref="div"/>
      <xs:element ref="hr"/>
      <xs:element ref="h1"/>
      <xs:element ref="h2"/>
      <xs:element ref="h3"/>
      <xs:element ref="h4"/>
      <xs:element ref="h5"/>
      <xs:element ref="h6"/>
      <xs:element ref="object"/>
      <xs:element ref="p"/>
      <xs:element ref="table"/>
    </xs:choice>
  </xs:group>

  <!-- definition of simple elements -->
  <xs:element name="br"/>
  <xs:element name="title" type="xs:string"/>

  <!-- definition of attributes -->
  <xs:attribute name="class" type="xs:string"/>
  <xs:attribute name="classid" type="xs:string"/>
  <xs:attribute name="colspan" type="xs:positiveInteger"/>
  <xs:attribute name="height" type="xs:nonNegativeInteger"/>
  <xs:attribute name="href" type="xs:string"/>
  <xs:attribute name="id" type="xs:string"/>
  <xs:attribute name="name" type="xs:string"/>
  <xs:attribute name="rowspan" type="xs:positiveInteger"/>
  <xs:attribute fixed="text/css" name="type" type="xs:string"/>
  <xs:attribute name="value" type="xs:string"/>

  <xs:attribute name="width">
    <xs:simpleType>
      <xs:restriction base="xs:string">
        <xs:pattern value="[\-+]?(\d+|\d+(\.\d+)?%)"/>
      </xs:restriction>
    </xs:simpleType>
  </xs:attribute>

  <!-- definition of complex elements -->
  <xs:element name="hr">
    <xs:complexType>
      <xs:attribute ref="width"/>
    </xs:complexType>
  </xs:element>

  <xs:element name="h1">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:string">
          <xs:attribute ref="class"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>

  <xs:element name="h2">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:string">
          <xs:attribute ref="class"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>

  <xs:element name="h3">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:string">
          <xs:attribute ref="class"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>

  <xs:element name="h4">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:string">
          <xs:attribute ref="class"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>

  <xs:element name="h5">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:string">
          <xs:attribute ref="class"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>

  <xs:element name="h6">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:string">
          <xs:attribute ref="class"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>

  <xs:element name="p">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:string">
          <xs:attribute ref="class"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>

  <xs:element name="a">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:string">
          <xs:attribute ref="href"/>
          <xs:attribute ref="id"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>

  <xs:element name="td">
    <xs:complexType>
      <xs:choice maxOccurs="unbounded" minOccurs="0">
        <xs:group ref="bodygroup"/>
      </xs:choice>
      <xs:attribute ref="class"/>
      <xs:attribute ref="width"/>
      <xs:attribute ref="rowspan"/>
      <xs:attribute ref="colspan"/>
    </xs:complexType>
  </xs:element>

  <xs:element name="tr">
    <xs:complexType>
      <xs:choice maxOccurs="unbounded" minOccurs="0">
        <xs:element ref="td"/>
        <xs:element name="div">
          <xs:complexType>
            <xs:choice maxOccurs="unbounded" minOccurs="0">
              <xs:element ref="td"/>
            </xs:choice>
            <xs:attribute ref="class" use="required"/>
          </xs:complexType>
        </xs:element>
      </xs:choice>
      <xs:attribute ref="class"/>
    </xs:complexType>
  </xs:element>

  <xs:element name="table">
    <xs:complexType>
      <xs:choice maxOccurs="unbounded" minOccurs="0">
        <xs:element ref="tr"/>
      </xs:choice>
      <xs:attribute ref="class"/>
      <xs:attribute ref="width"/>
    </xs:complexType>
  </xs:element>

  <xs:element name="param">
    <xs:complexType>
      <xs:attribute ref="name" use="required"/>
      <xs:attribute ref="value" use="required"/>
    </xs:complexType>
  </xs:element>

  <xs:element name="object">
    <xs:complexType>
      <xs:choice maxOccurs="unbounded" minOccurs="0">
        <xs:element ref="param"/>
      </xs:choice>
      <xs:attribute ref="classid" use="required"/>
      <xs:attribute ref="id"/>
      <xs:attribute ref="width"/>
      <xs:attribute ref="height"/>
      <xs:attribute ref="class"/>
    </xs:complexType>
  </xs:element>

  <xs:element name="style">
    <xs:complexType>
      <xs:simpleContent>
        <xs:extension base="xs:string">
          <xs:attribute ref="type"/>
        </xs:extension>
      </xs:simpleContent>
    </xs:complexType>
  </xs:element>

  <xs:element name="head">
    <xs:complexType>
      <xs:choice maxOccurs="unbounded" minOccurs="0">
        <xs:element ref="title"/>
        <xs:element minOccurs="0" ref="style"/>
      </xs:choice>
    </xs:complexType>
  </xs:element>

  <xs:element name="div">
    <xs:complexType>
      <xs:choice maxOccurs="unbounded" minOccurs="0">
        <xs:group ref="bodygroup"/>
      </xs:choice>
      <xs:attribute ref="class" use="required"/>
    </xs:complexType>
  </xs:element>

  <xs:element name="body">
    <xs:complexType>
      <xs:choice maxOccurs="unbounded" minOccurs="0">
        <xs:group ref="bodygroup"/>
      </xs:choice>
      <xs:attribute ref="class"/>
    </xs:complexType>
  </xs:element>

  <xs:element name="html">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="head"/>
        <xs:element ref="body"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>

</xs:schema>
''')


class CascadingStyleSheet(object):
    def __init__(self, defaults):
        # regular expression patterns for parsing
        self.tag_pattern = re.compile('([\w.#]+)\s*\{([^}]+)}')
        self.style_pattern = re.compile('([\w,-]+)\s*:\s*([\w,-,#]+)')
        self.style_dict = dict()
        self.parse_css(defaults)

    def parse_css(self, txt):
        tag_list = self.tag_pattern.findall(txt)
        for t in tag_list:
            tag = t[0]
            style_txt = t[1]
            if tag in self.style_dict:
                d = self.style_dict[tag]
            else:
                d = dict()
            style_list = self.style_pattern.findall(style_txt)
            for t in style_list:
                d[t[0]] = t[1]
            self.style_dict[tag] = d

    def get_tci_style(self, key, tag, cls=None, id=None):
        if id != None:
            s = tag + '#' + id
            if (s in self.style_dict) and (key in self.style_dict[s]):
                return self.style_dict[s][key]
            s = '#' + id
            if (s in self.style_dict) and (key in self.style_dict[s]):
                return self.style_dict[s][key]
        if cls != None:
            s = tag + '.' + cls
            if (s in self.style_dict) and (key in self.style_dict[s]):
                return self.style_dict[s][key]
            s = '.' + cls
            if (s in self.style_dict) and (key in self.style_dict[s]):
                return self.style_dict[s][key]
        return self.style_dict[tag][key]

    def get_style(self, key, element_list):
        for element in reversed(element_list):
            try:
                tag = element.tag
                cls = element.get('class')
                element_id = element.get('id')
                return self.get_tci_style(key, tag, cls, element_id)
            except KeyError:
                pass
        raise XMLError("Could not find style for element: key=%s tag=%s cls=%s id=%s." % (key, tag, cls, element_id))


class HtmlWindow(QtWidgets.QScrollArea):
    def __init__(self, parent, default_mod_name, logger=None):
        super(HtmlWindow, self).__init__(parent)
        self.parent = parent
        self.default_mod_name = default_mod_name
        self.logger = logger
        self.controls = dict()
        self.anonymous_controls = list()
        self.setup()

    def setup(self):
        self.frame = QtWidgets.QFrame()
        self.frame.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.main_sizer = QtWidgets.QVBoxLayout()
        self.frame.setLayout(self.main_sizer)
        self.setWidget(self.frame)
        self.setWidgetResizable(True)
        # the html element tree
        self.tree = None
        self.css = CascadingStyleSheet(default_style_sheet)
        self.anchor_dict = dict()
        self.row_stack = list()

    def reset(self):
        # clear the layout
        self.frame.hide()
        self.frame.deleteLater()
        self.controls = dict()
        self.anonymous_controls = list()
        self.setup()

    def open_file(self, filename):
        self.frame.hide()
        # load and parse the file
        if lxml_loaded:
            parser = ElementTree.ETCompatXMLParser()
            self.tree = ElementTree.parse(filename, parser=parser)
        else:
            self.tree = ElementTree.parse(filename)
        # validate the file if lxml is available
        if lxml_loaded:
            xmlschema_tree = ElementTree.parse(xmlschema_f)
            xmlschema = ElementTree.XMLSchema(xmlschema_tree)
            xmlschema.assertValid(self.tree)
        root = self.tree.getroot()
        self.layout(root, list(), self.main_sizer)
        self.frame.show()
        return self.anonymous_controls, self.controls

    def extract_size(self, attrs):
        object_width = -1
        object_proportion = 0
        if 'width' in attrs:
            width = attrs.pop('width')
            if '%' in width:
                object_proportion = float(width.strip('%'))
            else:
                object_width = int(width)
        object_height = -1
        if 'height' in attrs:
            object_height = int(attrs.pop('height'))
        return (object_width, object_height, object_proportion)

    def get_padding(self, element_list):
        pad = self.css.get_style('padding', element_list)
        pads = pad.split()
        if len(pads) == 1:
            return int(pads[0].strip('px')), int(pads[0].strip('px'))
        elif len(pads) == 2:
            return int(pads[0].strip('px')), int(pads[1].strip('px'))
        else:
            raise XMLError("Unrecognized padding: %s." % pad)

    def get_font(self, element_list):
        font_size = int(self.css.get_style('font-size', element_list).strip('pt'))
        font_family = self.css.get_style('font-family', element_list)
        font_style = self.css.get_style('font-style', element_list)
        font_weight = self.css.get_style('font-weight', element_list)
        # italics
        if font_style == 'italic':
            italic = True
        else:
            italic = False
        # weight
        if font_weight == 'bold':
            weight = 75
        elif font_weight == 'light':
            weight = 25
        else:
            weight = 50
        font = QtGui.QFont(font_family, font_size, weight, italic)
        return font

    def layout(self, element, element_list, sizer):
        tag = element.tag
        if tag == 'html':
            el = element_list[:]
            el.append(element)
            for subelement in element:
                self.layout(subelement, el, sizer)
            return
        elif tag == 'head':
            el = element_list[:]
            el.append(element)
            for subelement in element:
                self.layout(subelement, el, sizer)
            return
        elif tag == 'title':
            self.set_title(element.text)
            return
        elif tag == 'style':
            self.css.parse_css(element.text)
            return
        elif tag == 'body':
            el = element_list[:]
            el.append(element)
            bg_color = QtGui.QColor(self.css.get_style('background-color', el))
            html_palette = QtGui.QPalette()
            html_palette.setColor(QtGui.QPalette.Window, bg_color)
            self.setPalette(html_palette)
            self.setBackgroundRole(QtGui.QPalette.Window)
            # set margins and borders
            bdr = int(self.css.get_style('margin', el).strip('px'))
            sizer.setContentsMargins(bdr, bdr, bdr, bdr)
            v_pad, h_pad = self.get_padding(el)
            sizer.setSpacing(v_pad)
            # layout the body contents
            self.row_begin(el, sizer)
            self.row_layout(element, el, sizer)
            self.row_end()
            # stretch space on the bottom to take up and extra vertical space
            sizer.addStretch(1.0)
            return
        elif tag == 'br':
            el = element_list[:]
            el.append(element)
            # end this row and start the next one
            self.row_end()
            self.row_begin(el, sizer)
            return
        elif tag == 'div':
            el = element_list[:]
            el.append(element)
            for subelement in element:
                self.layout(subelement, el, sizer)
            return
        elif tag == 'table':
            el = element_list[:]
            el.append(element)
            self.row_end()
            self.row_begin(element_list, sizer)
            width, height, proportion = self.extract_size(element.attrib)
            table_sizer = QtWidgets.QGridLayout()
            v_pad, h_pad = self.get_padding(el)
            table_sizer.setVerticalSpacing(v_pad)
            table_sizer.setHorizontalSpacing(h_pad)
            row_sizer = self.row_get_sizer()
            row_sizer.addLayout(table_sizer, proportion)
            row = 0
            col = 0
            for subelement in element:
                row, col = self.table_layout(subelement, table_sizer, el, row, col)
            align = self.css.get_style('align', el)
            self.row_set_align_and_proportion(align, proportion)
            self.row_end()
            self.row_begin(element_list, sizer)
            return
        elif tag == 'a':
            el = element_list[:]
            el.append(element)
            if 'href' in element.attrib:
                ob = Hyperlink(self, label=element.text,
                                url=element.attrib['href'].strip('#'))
                ob.setFont(self.get_font(el))
                row_sizer = self.row_get_sizer()
                row_sizer.addWidget(ob, 0, QtCore.Qt.AlignBottom)
                align = self.css.get_style('align', el)
                self.row_set_align_and_proportion(align, 0)
                return
            else:
                key = element.attrib['id']
                self.anchor_dict[key] = self.row_get_sizer()
                align = self.css.get_style('align', el)
                self.row_set_align_and_proportion(align, 0)
                return
        elif tag == 'p':
            el = element_list[:]
            el.append(element)
            ob = QtWidgets.QLabel(element.text)
            ob.setFont(self.get_font(el))
            row_sizer = self.row_get_sizer()
            row_sizer.addWidget(ob, 0, QtCore.Qt.AlignBottom)
            align = self.css.get_style('align', el)
            self.row_set_align_and_proportion(align, 0)
            return
        elif tag == 'h1' or tag == 'h2' or tag == 'h3' or tag == 'h4' or tag == 'h5' or tag == 'h6':
            el = element_list[:]
            el.append(element)
            self.row_end()
            self.row_begin(element_list, sizer)
            ob = QtWidgets.QLabel(element.text)
            ob.setFont(self.get_font(el))
            row_sizer = self.row_get_sizer()
            row_sizer.addWidget(ob, 0, QtCore.Qt.AlignBottom)
            align = self.css.get_style('align', el)
            self.row_set_align_and_proportion(align, 50)
            self.row_end()
            self.row_begin(element_list, sizer)
            return
        elif tag == 'object':
            el = element_list[:]
            el.append(element)
            row_sizer = self.row_get_sizer()
            # lxml docs say to do this to make a copy of the attribute dictionary
            attr_dict = dict(element.attrib)
            width, height, proportion = self.extract_size(attr_dict)
            full_object_name = attr_dict.pop('classid')
            if 'id' in attr_dict:
                element_id = attr_dict.pop('id')
            else:
                element_id = None
            for p in element.getiterator(tag='param'):
                attr_dict[p.get('name')] = p.get('value')
            evaled_attrs = dict()
            for k, v in attr_dict.items():
                try:
                    evaled_attrs[k] = eval(v, globals())
                except Exception:
                    evaled_attrs[k] = v
            try:
                name_list = full_object_name.split('.')
                if len(name_list) > 1:
                    mod_name = '.'.join(name_list[0:-1])
                else:
                    mod_name = self.default_mod_name
                object_name = name_list[-1]
                try:
                    # try to import from pythics first
                    mod = importlib.import_module('pythics.' + mod_name)
                except ImportError:
                    # if not found, search globally for module
                    mod = importlib.import_module(mod_name)
                ob = getattr(mod, object_name)(parent=self, **evaled_attrs)
                if isinstance(ob, QtWidgets.QWidget):
                    widget = ob
                elif hasattr(ob, '_widget'):
                    widget = ob._widget
                else:
                    widget = None
                if widget is not None:
                    if width > 0:
                        widget.setFixedWidth(width)
                    if height > 0:
                        widget.setFixedHeight(height)
                    row_sizer.addWidget(widget, proportion, QtCore.Qt.AlignBottom)
                # store the widget
                if element_id is not None:
                    self.controls[element_id] = ob
                else:
                    self.anonymous_controls.append(ob)
            except ImportError:
                if element_id is not None:
                    s = '%s, id: %s' % (full_object_name, element_id)
                else:
                    s = full_object_name
                ss = "Error importing xml object '%s'. The library is not available." % s
                #if self.logger is not None:
                #    self.logger.warning(ss)
                load_error = True
            except:
                if element_id is not None:
                    s = '%s, id: %s' % (full_object_name, element_id)
                else:
                    s = full_object_name
                ss = "Error initializing xml object '%s'." % s
                ss = ss + '\n' + traceback.format_exc(1)
                #if self.logger is not None:
                #    self.logger.exception(ss)
                load_error = True
            else:
                load_error = False
            if load_error:
                error_box = QtWidgets.QTextEdit()
                error_box.setReadOnly(True)
                palette = QtGui.QPalette()
                palette.setColor(QtGui.QPalette.Base, QtGui.QColor('red'))
                error_box.setPalette(palette)
                error_box.setBackgroundRole(QtGui.QPalette.Base)
                error_box.setPlainText(ss)
                if width > 0:
                    error_box.setFixedWidth(width)
                if height > 0:
                    error_box.setFixedHeight(height)
                row_sizer.addWidget(error_box, proportion, QtCore.Qt.AlignBottom)
            align = self.css.get_style('align', el)
            self.row_set_align_and_proportion(align, proportion)
            return
        elif tag == 'hr':
            # end this row, insert horizontal line, and start the next row
            self.row_end()
            self.row_begin(element_list, sizer)
            ob = QtWidgets.QFrame()
            ob.setFrameStyle(QtWidgets.QFrame.HLine|QtWidgets.QFrame.Sunken)
            row_sizer = self.row_get_sizer()
            row_sizer.addWidget(ob, 1, QtCore.Qt.AlignBottom)
            self.row_set_align_and_proportion('left', 100)
            self.row_end()
            self.row_begin(element_list, sizer)
            return
        else:
            raise XMLError("Unrecognized tag: %s." % tag)

    def row_begin(self, element_list, sizer):
        # start new row
        row_sizer = QtWidgets.QHBoxLayout()
        v_pad, h_pad = self.get_padding(element_list)
        row_sizer.setSpacing(h_pad)
        sizer.addLayout(row_sizer)
        total_align = self.css.get_style('align', element_list) # default
        if total_align == None:
            total_align = 'left'
        self.row_stack.append((row_sizer, total_align, 0))
        return

    def row_layout(self, element, element_list, sizer):
        for subelement in element:
            self.layout(subelement, element_list, sizer)

    def row_get_sizer(self):
        return self.row_stack[-1][0]

    def row_set_align_and_proportion(self, sub_align, sub_proportion):
        last_sizer, total_align, total_proportion = self.row_stack[-1]
        if sub_align != None:
            total_align = sub_align
        total_proportion += sub_proportion
        self.row_stack[-1] = (last_sizer, total_align, total_proportion)

    def row_end(self):
        row_sizer, total_align, total_prop = self.row_stack.pop()
        needed_row_proportion = 100.0 - total_prop
        if needed_row_proportion > 0:
            if total_align == 'left':
                row_sizer.insertStretch(-1, needed_row_proportion)
            elif total_align == 'center':
                row_sizer.insertStretch(0, needed_row_proportion/2.0)
                row_sizer.insertStretch(-1, needed_row_proportion/2.0)
            elif total_align == 'right':
                row_sizer.insertStretch(0, needed_row_proportion)
            else:
                raise XMLError("Unrecognized alignment: %s." % total_align)
        return

    def table_layout(self, element, table_sizer, element_list, row, col):
        tag = element.tag
        if tag == 'tr':
            col = 0
            el = element_list[:]
            el.append(element)
            for subelement in element:
                row, col = self.table_layout(subelement, table_sizer, el, row, col)
            row += 1
            return row, col
        elif tag == 'td':
            el = element_list[:]
            el.append(element)
            if 'colspan' in element.attrib:
                colspan = int(element.attrib['colspan'])
            else:
                colspan = 1
            if 'rowspan' in element.attrib:
                rowspan = int(element.attrib['rowspan'])
            else:
                rowspan = 1
            sizer = QtWidgets.QVBoxLayout()
            v_pad, h_pad = self.get_padding(el)
            sizer.setSpacing(v_pad)
            table_sizer.addLayout(sizer, row, col, rowspan, colspan,
                            QtCore.Qt.AlignBottom)
            self.row_begin(el, sizer)
            self.row_layout(element, el, sizer)
            self.row_end()
            width, height, proportion = self.extract_size(element.attrib)
            if proportion > 0:
                table_sizer.setColumnStretch(col, proportion)
            col += colspan
            return row, col
        else:
            raise XMLError("Unrecognized tag: %s." % tag)

    def scroll_to_anchor(self, name):
        position = self.anchor_dict[name].geometry()
        #bar->setValue(bar->maximum())
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        self.ensureVisible(position.left(), position.top())

    def set_title(self, title):
        # to be overriden by subclasses
        pass

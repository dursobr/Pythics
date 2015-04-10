# -*- coding: utf-8 -*-
#
# Copyright 2008 - 2015 Brian R. D'Urso
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
import getopt
import inspect
import logging
import os, os.path
import multiprocessing
import pickle
import sys, traceback

#from PyQt4 import QtGui
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


import pythics.html
import pythics.libcontrol
import pythics.master


#
# Application top level window
#   one for the whole application
#   parent of all TabFrame instances
#
class MainWindow(QtGui.QMainWindow):
    def __init__(self, master, app, parent=None, fixed_tabs=False):
        super(MainWindow, self).__init__(parent)
        # pythics data
        self.master = master
        self.app = app
        self.fixed_tabs = fixed_tabs
        self.workspace = ''
        # setup window basics
        self.resize(900, 560)
        self.setWindowTitle('Pythics')
        self.clipboard = QtGui.QApplication.clipboard()
        # set the corner icon
        icon = QtGui.QIcon(os.path.join(sys.path[0], 'pythics_icon.ico'))
        self.setWindowIcon(icon)
        # add the menu bar
        self.new_menu_bar()
        # fill in the main window
        self.new_tab_frame()
        # add the status bar
        self.new_status_bar()
        # for printing later
        # high resolution printer give error when printing:
        #   QPainter::begin: Paint device returned engine == 0, type: 2
        #self.printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        self.printer = QtGui.QPrinter()

    def confirm_exit(self):
        reply = QtGui.QMessageBox.question(self, 'Confirm',
            'Are you sure you want to exit?', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            return True
        else:
            return False

    def confirm_close(self):
        reply = QtGui.QMessageBox.question(self, 'Confirm',
            'Are you sure you want to close the VI?', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            return True
        else:
            return False

    def closeEvent(self, event):
        # called when the close button on the window is pushed
        if self.confirm_exit():
            self.shutdown()
            event.accept()
        else:
            event.ignore()

    def new_status_bar(self):
        self.status_text = QtGui.QLabel('')
        self.statusBar().addWidget(self.status_text, 1)

    def set_status_text(self, value):
        self.status_text.setText(value)

    def new_tab_frame(self):
        self.tab_frame = QtGui.QTabWidget()
        self.tab_frame.setDocumentMode(True)
        self.tab_frame.setTabsClosable(not self.fixed_tabs)
        self.tab_frame.setMovable(not self.fixed_tabs)
        self.tab_frame.currentChanged.connect(self.redraw)
        self.tab_frame.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_frame)

    def redraw(self, index):
        if self.tab_frame.widget(index) == None:
            title = 'Pythics'
        else:
            title = self.tab_frame.widget(index).title
            self.tab_frame.widget(index).redraw()
        self.setWindowTitle(title)

    def get_active_tab(self):
        return self.tab_frame.currentWidget()

    def close_tab(self, i):
        if self.confirm_close():
            self.tab_frame.widget(i).close()
            self.tab_frame.removeTab(i)
        if self.tab_frame.count() == 0:
            self.disable_menu_items()

    def get_open_filename(self, name_filter='*.*', directory='', title='Select a file to open'):
        filename = QtGui.QFileDialog.getOpenFileName(self, title, directory, name_filter)
        if USES_PYSIDE:
            # PySide returns a tuple instead of just a string
            filename = filename[0]
        if filename == '':
            raise IOError('No file selected.')
        return filename

    def get_save_filename(self, name_filter='*.*', directory='', title='Select a filename for saving'):
        filename = QtGui.QFileDialog.getSaveFileName(self, title, directory, name_filter)
        if filename == '':
            raise IOError('No filename selected.')
        return filename

    def add_menu(self, name):
        self.last_menu = self.menuBar().addMenu(name)
        return self.last_menu

    def add_menu_item(self, item_string, item_function, shortcut=0, tip=''):
        action = self.last_menu.addAction(item_string, item_function, shortcut)
        action.setStatusTip(tip)
        return action

    def add_menu_seperator(self):
        self.last_menu.addSeparator()

    def new_menu_bar(self):
        # File menu
        self.file_menu = self.add_menu('&File')
        self.add_menu_item('&Open...', self.menu_open, 'Ctrl+O',
                            'Open a vi file.')
        self.add_menu_item('&Close', self.menu_close, 'Ctrl+W',
                            'Close the current vi.')
        self.add_menu_item('Close All', self.menu_close_all, 0,
                            'Close all open files.')
        self.add_menu_item('&Reload', self.menu_reload, 'Ctrl+R',
                            'Reload the vi.')
        self.add_menu_seperator()
        self.add_menu_item('Open Workspace...', self.menu_open_workspace, 0,
                            'Open a group of files (a workspace).')
        self.add_menu_item('Save Workspace', self.menu_save_workspace, 0,
                            'Save open workspace.')
        self.add_menu_item('Save Workspace As...', self.menu_save_workspace_as,
                            0, 'Save open files as a workspace.')
        self.add_menu_seperator()
        self.add_menu_item('Page Set&up...', self.menu_page_setup, 0,
                            'Page setup for printing.')
        self.add_menu_item('Print Pre&view', self.menu_print_preview, 0,
                            'Preview pages to be printed.')
        self.add_menu_item('&Print...', self.menu_print, 0,
                            'Print the current html.')
        self.add_menu_seperator()
        self.add_menu_item('E&xit', self.menu_quit, 0, 'Quit Pythics')
        # Edit menu
        self.edit_menu = self.add_menu('&Edit')
        self.add_menu_item('Cu&t', self.menu_cut, 'Ctrl+X',
                            'Cut text to clipboard.')
        self.add_menu_item('&Copy', self.menu_copy, 'Ctrl+C',
                            'Copy text to clipboard.')
        self.add_menu_item('&Paste', self.menu_paste, 'Ctrl+V',
                            'Paste text from clipboard.')
        self.add_menu_item('Delete', self.menu_delete, 0,
                            'Delete selected text.')
        # Parameters menu
        self.param_menu = self.add_menu('&Parameters')
        self.add_menu_item('Load Defaults', self.menu_load_parameters_defaults,
                            0, 'Load default parameters.')
        self.add_menu_item('Load...', self.menu_load_parameters, 0,
                            'Load parameter file')
        self.add_menu_seperator()
        self.add_menu_item('Save As Defaults',
                            self.menu_save_parameters_as_defaults,
                            0, 'Save parameters to default location.')
        self.add_menu_item('Save As...', self.menu_save_parameters_as, 0,
                            'Save parameter file.')
        # Help menu
        if not self.fixed_tabs:
            self.help_menu = self.add_menu('&Help')
            self.add_menu_item('About Pythics...', self.menu_about,
                                0, '')
            self.add_menu_item('Open Help', self.menu_help,
                                0, '')
        self.disable_menu_items()

    def disable_menu_items(self):
        if self.fixed_tabs:
            self.file_menu.actions()[0].setEnabled(False)
            self.file_menu.actions()[5].setEnabled(False)
        # disable menu items that require an open tab
        self.file_menu.actions()[1].setEnabled(False)
        self.file_menu.actions()[2].setEnabled(False)
        self.file_menu.actions()[3].setEnabled(False)
        self.file_menu.actions()[6].setEnabled(False)
        self.file_menu.actions()[7].setEnabled(False)
        self.file_menu.actions()[10].setEnabled(False)
        self.file_menu.actions()[11].setEnabled(False)
        self.param_menu.actions()[0].setEnabled(False)
        self.param_menu.actions()[1].setEnabled(False)
        self.param_menu.actions()[3].setEnabled(False)
        self.param_menu.actions()[4].setEnabled(False)

    def enable_menu_items(self):
        # enable menu items that require an open tab
        if self.fixed_tabs:
            self.file_menu.actions()[3].setEnabled(True)
            self.file_menu.actions()[10].setEnabled(True)
            self.file_menu.actions()[11].setEnabled(True)
            self.param_menu.actions()[0].setEnabled(True)
            self.param_menu.actions()[1].setEnabled(True)
            self.param_menu.actions()[3].setEnabled(True)
            self.param_menu.actions()[4].setEnabled(True)
        else:
            self.file_menu.actions()[1].setEnabled(True)
            self.file_menu.actions()[2].setEnabled(True)
            self.file_menu.actions()[3].setEnabled(True)
            self.file_menu.actions()[6].setEnabled(True)
            self.file_menu.actions()[7].setEnabled(True)
            self.file_menu.actions()[10].setEnabled(True)
            self.file_menu.actions()[11].setEnabled(True)
            self.param_menu.actions()[0].setEnabled(True)
            self.param_menu.actions()[1].setEnabled(True)
            self.param_menu.actions()[3].setEnabled(True)
            self.param_menu.actions()[4].setEnabled(True)

    def menu_open(self):
        try:
            filename = self.get_open_filename('xml (*.htm *.html *.xml)')
        except IOError:
            pass
        else:
            self.open_html_file(filename)
            self.enable_menu_items()

    def menu_close(self):
        if self.confirm_close():
            self.get_active_tab().close()
            self.tab_frame.removeTab(self.tab_frame.currentIndex())
            if self.tab_frame.count() == 0:
                self.disable_menu_items()

    def menu_close_all(self):
        reply = QtGui.QMessageBox.question(self, 'Confirm',
            'Are you sure you want to close all tabs?', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            while self.tab_frame.count() > 0:
                self.get_active_tab().close()
                self.tab_frame.removeTab(self.tab_frame.currentIndex())
            if self.tab_frame.count() == 0:
                self.disable_menu_items()

    def menu_quit(self):
        if self.confirm_exit():
            self.shutdown()
            self.app.quit()

    def menu_reload(self):
        reply = QtGui.QMessageBox.question(self, 'Confirm',
            'Are you sure you want to reload the VI?', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            tab_window = self.get_active_tab()
            title = tab_window.reload_file()
            index = self.tab_frame.currentIndex()
            self.tab_frame.setTabText(index, title)

    def menu_open_workspace(self):
        try:
            filename = self.get_open_filename('pickle file (*.pkl *.txt)')
        except IOError:
            pass
        else:
            self.open_workspace(filename)
            self.workspace = filename
            self.enable_menu_items()

    def menu_save_workspace(self):
        if self.workspace == '':
            try:
                filename = self.get_save_filename('*.pkl')
            except IOError:
                pass
            else:
                self.save_workspace(filename)
                self.workspace = filename
        else:
            self.save_workspace(filename=self.workspace)

    def menu_save_workspace_as(self):
        try:
            filename = self.get_save_filename('*.pkl')
        except IOError:
            pass
        else:
            self.save_workspace(filename)
            self.workspace = filename

    def menu_page_setup(self):
        dialog = QtGui.QPageSetupDialog(self.printer)
        dialog.exec_()

    def menu_print_preview(self):
        dialog = QtGui.QPrintPreviewDialog(self.printer)
        dialog.paintRequested.connect(self.print_current_tab)
        dialog.exec_()

    def menu_print(self):
        dialog = QtGui.QPrintDialog(self.printer)
        dialog.setWindowTitle('Print Document')
        if dialog.exec_() == QtGui.QDialog.Accepted:
            self.statusBar().showMessage('Printing...')
            self.print_current_tab(self.printer)
            self.statusBar().clearMessage()

    def print_current_tab(self, printer):
        scroll_area = self.get_active_tab()
        # overall scale: set to fill width of page
        page_width = printer.pageRect().width()
        hsb = scroll_area.horizontalScrollBar()
        frame_width = hsb.maximum() + hsb.pageStep()
        scale = float(page_width)/float(frame_width)
        x_offset = 0
        sb = scroll_area.verticalScrollBar()
        y_offset = - scale*sb.sliderPosition()
        p = QtGui.QPainter(printer)
        p.setRenderHints(QtGui.QPainter.Antialiasing
                        | QtGui.QPainter.TextAntialiasing
                        | QtGui.QPainter.SmoothPixmapTransform, True)
        p.translate(x_offset, y_offset)
        p.scale(scale, scale)
        scroll_area.frame.render(p)
        p.end()

    def menu_cut(self):
        w = self.app.focusWidget()
        try:
            w.cut()
        except:
            pass

    def menu_copy(self):
        w = self.app.focusWidget()
        try:
            w.copy()
        except:
            pass

    def menu_paste(self):
        w = self.app.focusWidget()
        try:
            w.paste()
        except:
            pass

    def menu_delete(self):
        w = self.app.focusWidget()
        t = self.clipboard.text()
        try:
            w.cut()
        except:
            pass
        self.clipboard.setText(t)

    def menu_load_parameters_defaults(self):
        tab_window = self.get_active_tab()
        reply = QtGui.QMessageBox.question(self, 'Confirm Load Parameters',
            'Are you sure you want to replace current parameters?',
            QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            tab_window.load_parameters(default=True)

    def menu_load_parameters(self):
            self.get_active_tab().load_parameters()

    def menu_save_parameters_as_defaults(self):
        self.get_active_tab().save_parameters(default=True)

    def menu_save_parameters_as(self):
        self.get_active_tab().save_parameters()

    def shutdown(self):
        # stop all action threads then exit
        self.set_status_text('Waiting for threads and subprocesses to die...')
        self.master.stop()

    def open_html_file(self, filename):
        self.tab_frame.setUpdatesEnabled(False)
        new_tab_window = TabHtmlWindow(self, self.master)
        # set current working directory
        directory = os.path.dirname(filename)
        if directory != '':
            os.chdir(directory)
        title = new_tab_window.open_file(filename)
        index = self.tab_frame.addTab(new_tab_window, title)
        self.tab_frame.setCurrentIndex(index)
        self.tab_frame.setUpdatesEnabled(True)

    def open_workspace(self, filename):
        with open(filename, 'r') as file:
            file_list = pickle.load(file)
        for f in file_list:
            # set current working directory
            os.chdir(os.path.dirname(f))
            # open the file
            self.open_html_file(f)
        self.enable_menu_items()

    def save_workspace(self, filename):
        tf = self.tab_frame
        l = list([])
        initial_index = tf.currentIndex()
        n_pages = tf.count()
        self.tab_frame.setUpdatesEnabled(False)
        for i in range(n_pages):
            tf.setCurrentIndex(i)
            html_filename = tf.currentWidget().html_file
            l.append(html_filename)
        with open(filename, 'w') as file:
            pickle.dump(l, file, 0)
        tf.setCurrentIndex(initial_index)
        self.tab_frame.setUpdatesEnabled(True)

    def menu_about(self):
        QtGui.QMessageBox.about(self, 'About Pythics',
"""Python Instrument Control System, also known as Pythics
version 0.7.3

Copyright 2008 - 2015 Brian R. D'Urso

Pythics is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.

Pythics is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public
License along with Pythics. If not, see
<http://www.gnu.org/licenses/>.""")

    def menu_help(self):
        # build the path to the help file
        directory = os.path.dirname(inspect.getfile(pythics))
        filename = os.path.join(directory, 'help', 'help.xml')
        # open it
        self.open_html_file(filename)
        self.enable_menu_items()


#
# TabHtmlWindow - one for each primary html file
#
class TabHtmlWindow(pythics.html.HtmlWindow):
    def __init__(self, parent, master):
        self.main_window = parent
        self.master = master
        self.title = None
        super(TabHtmlWindow, self).__init__(parent, 'pythics.controls',
                                            multiprocessing.get_logger())
        # force widgets to redraw when the scrollbars are released
        #   this is needed for animated matplotlib widgets
        self.verticalScrollBar().sliderReleased.connect(self.redraw)
        self.horizontalScrollBar().sliderReleased.connect(self.redraw)

    def redraw(self):
        if not self.error:
            self.process.redraw()

    def close(self):
        if not self.error:
            try:
                self.master.stop_slave_process(self.process)
            except Exception:
                self.logger.exception('Error while closing process.')

    def set_title(self, title):
        self.title = title

    def open_file(self, filename):
        self.error = False
        try:
            self.main_window.set_status_text('Loading file %s.' % filename)
            self.html_file = filename
            self.html_path, file_name_only = os.path.split(filename)
            self.default_parameter_filename = 'defaults.txt'
            anonymous_controls, controls = pythics.html.HtmlWindow.open_file(self, filename)
            self.process = self.master.new_slave_process( self.html_path, file_name_only, anonymous_controls, controls)
            self.process.start()
        except:
            message = 'Error while opening xml file %s\n' % file_name_only  + traceback.format_exc(0)
            QtGui.QMessageBox.critical(self, 'Error', message, QtGui.QMessageBox.Ok)
            self.logger.exception('Error while opening xml file.')
            self.error = True
        self.main_window.set_status_text('')
        if self.title is None:
            self.title = file_name_only
            self.set_title(self.title)
        return self.title

    def reload_file(self):
        self.close()
        self.reset()
        # set current working directory
        os.chdir(os.path.dirname(self.html_file))
        return self.open_file(self.html_file)

    # parameter save and recall functions for internal use
    def load_parameters(self, filename='', default=False):
        if not self.error:
            try:
                if default:
                    if not os.path.isabs(self.default_parameter_filename):
                        filename = os.path.join(self.html_path,
                                        self.process.default_parameter_filename)
                else:
                    if filename == '':
                        filename = self.main_window.get_open_filename('data (*.*)')
                    elif not os.path.isabs(filename):
                        filename = os.path.join(self.html_path, filename)
                if filename != '':
                    try:
                        self.process.load_parameters(filename)
                    except IOError as error:
                        (errno, strerror) = error.args
                        self.logger.error('Error (%s) opening parameter file: %s.' % (errno, strerror))
            except:
                self.logger.exception('Error while loading parameters.')

    def save_parameters(self, filename='', default=False):
        if not self.error:
            try:
                if default:
                    if not os.path.isabs(self.default_parameter_filename):
                        filename = os.path.join(self.html_path,
                                        self.process.default_parameter_filename)
                else:
                    if filename == '':
                        filename = self.main_window.get_save_filename('data (*.*)')
                    elif not os.path.isabs(filename):
                        filename = os.path.join(self.html_path, filename)
                if filename != '':
                        self.process.save_parameters(filename)
            except:
                self.logger.exception('Error while loading parameters.')


class OptionsProcessor(object):
    def __init__(self):
        self.multiprocess_manager = multiprocessing.Manager()
        # configure the logger
        self.logger = multiprocessing.log_to_stderr()
        #self.logger.setLevel(logging.DEBUG)
        #self.logger.setLevel(logging.INFO)
        self.logger.setLevel(logging.WARNING)
        self.first_vi = ""

    def usage(self):
        print """\
Usage: pythics-run.py [options]
Options:
  -h | --help    show help text then exit
  -a | --app     selects startup html file
  -v | --verbose selects verbose mode
  -d | --debug   selects debug mode"""

    def options(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'ha:vd',
                                       ['help', 'app', 'verbose', 'debug'])
        except getopt.GetoptError, err:
            # print help information and exit:
            print(err) # will print something like "option -a not recognized"
            self.usage()
            sys.exit(2)
        for o, a in opts:
            if o in ('-v', '--verbose'):
                self.logger.setLevel(logging.INFO)
            elif o in ('"-d', '--debug'):
                self.logger.setLevel(logging.DEBUG)
            elif o in ('-h', '--help'):
                self.usage()
                sys.exit(0)
            elif o in ('-a', '--app'):
                self.logger.info('starting ' + a)
                self.first_vi = a
            else:
                assert False, 'unhandled option'


#
# create and start the application
#
if __name__ == '__main__':
    application = QtGui.QApplication(sys.argv)
    master = pythics.master.Master()
    cl_options_processor = OptionsProcessor()
    cl_options_processor.options()
    window = MainWindow(master, application)
    window.show()
    master.start()
    if os.path.isfile(cl_options_processor.first_vi):
        window.open_html_file(cl_options_processor.first_vi)
    application.exec_()

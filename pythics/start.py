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
import getopt
import inspect
import logging
import os, os.path
import multiprocessing
import pickle
import sys, traceback

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
import pythics.parent


#
# Application top level window
#   one for the whole application
#   parent of all TabFrame instances
#
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent_process, app, parent=None, compact=False):
        super(MainWindow, self).__init__(parent)
        # pythics data
        self.parent_process = parent_process
        self.app = app
        self.compact = compact
        self.fixed_tabs = compact
        self.workspace = ''
        self.shutdown_on_exit = False
        # setup window basics
        #self.resize(900, 560)
        # match raspberry pi touchscreen size
        self.resize(800, 480)
        self.setWindowTitle('Pythics')
        self.clipboard = QtWidgets.QApplication.clipboard()
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
        self.printer = QtPrintSupport.QPrinter()

    def confirm_exit(self):
        reply = QtWidgets.QMessageBox.question(self, 'Confirm',
            'Are you sure you want to exit?', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            return True
        else:
            return False

    def confirm_close(self):
        reply = QtWidgets.QMessageBox.question(self, 'Confirm',
            'Are you sure you want to close the app?', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
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
        if not self.compact:
            self.status_text = QtWidgets.QLabel('')
            self.statusBar().addWidget(self.status_text, 1)

    def set_status_text(self, value):
        if not self.compact:
            self.status_text.setText(value)

    def new_tab_frame(self):
        self.tab_frame = QtWidgets.QTabWidget()
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
        filename = QtWidgets.QFileDialog.getOpenFileName(self, title, directory, name_filter)[0]
        if filename == '':
            raise IOError('No file selected.')
        return filename

    def get_save_filename(self, name_filter='*.*', directory='', title='Select a filename for saving'):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, title, directory, name_filter)[0]
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
                            'Open an app file.')
        self.add_menu_item('&Close', self.menu_close, 'Ctrl+W',
                            'Close the current app.')
        self.add_menu_item('Close All', self.menu_close_all, 0,
                            'Close all open files.')
        self.add_menu_item('&Reload', self.menu_reload, 'Ctrl+R',
                            'Reload the app.')
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

    def menu_close(self):
        if self.confirm_close():
            self.get_active_tab().close()
            self.tab_frame.removeTab(self.tab_frame.currentIndex())
            if self.tab_frame.count() == 0:
                self.disable_menu_items()

    def menu_close_all(self):
        reply = QtWidgets.QMessageBox.question(self, 'Confirm',
            'Are you sure you want to close all tabs?', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            while self.tab_frame.count() > 0:
                self.get_active_tab().close()
                self.tab_frame.removeTab(self.tab_frame.currentIndex())
            if self.tab_frame.count() == 0:
                self.disable_menu_items()

    def menu_quit(self):
        if self.confirm_exit():
            self.shutdown()
            self.app.quit()
            if self.shutdown_on_exit:
                os.system("shutdown -h now")

    def menu_reload(self):
        reply = QtWidgets.QMessageBox.question(self, 'Confirm',
            'Are you sure you want to reload the app?', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
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
        dialog = QtPrintSupport.QPageSetupDialog(self.printer)
        dialog.exec_()

    def menu_print_preview(self):
        dialog = QtPrintSupport.QPrintPreviewDialog(self.printer)
        dialog.paintRequested.connect(self.print_current_tab)
        dialog.exec_()

    def menu_print(self):
        dialog = QtPrintSupport.QPrintDialog(self.printer)
        dialog.setWindowTitle('Print Document')
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.set_status_text('Printing...')
            self.print_current_tab(self.printer)
            self.set_status_text('')

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
#        # direct printing - comes out fuzzy
#        painter = QtGui.QPainter(printer)
#        painter.setRenderHints(QtGui.QPainter.Antialiasing
#                        | QtGui.QPainter.TextAntialiasing
#                        | QtGui.QPainter.SmoothPixmapTransform, True)
#        painter.translate(x_offset, y_offset)
#        painter.scale(scale, scale)
#        scroll_area.frame.render(painter, QtCore.QPoint())
#        painter.end()
        # indirect printing: print to picture and then to printer 
        #   for sharper output from many controls
        # first draw to the QPicture
        picture = QtGui.QPicture()
        picture_painter = QtGui.QPainter(picture)
        picture_painter.translate(x_offset, y_offset)
        picture_painter.scale(scale, scale)
        scroll_area.frame.render(picture_painter, QtCore.QPoint(0, 0))
        picture_painter.end();
        # then draw the QPicture to the printer
        painter = QtGui.QPainter(printer)
        painter.drawPicture(QtCore.QPoint(0, 0), picture);
        painter.end()
        

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
        reply = QtWidgets.QMessageBox.question(self, 'Confirm Load Parameters',
            'Are you sure you want to replace current parameters?',
            QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
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
        self.parent_process.stop()

    def open_html_file(self, filename):
        self.tab_frame.setUpdatesEnabled(False)
        new_tab_window = TabHtmlWindow(self, self.parent_process)
        # set current working directory
        directory = os.path.dirname(filename)
        if directory != '':
            os.chdir(directory)
        title = new_tab_window.open_file(filename)
        index = self.tab_frame.addTab(new_tab_window, title)
        self.tab_frame.setCurrentIndex(index)
        self.tab_frame.setUpdatesEnabled(True)
        self.enable_menu_items()

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
        QtWidgets.QMessageBox.about(self, 'About Pythics',
"""Python Instrument Control System, also known as Pythics
version 1.0.0

Copyright 2008 - 2019 Brian R. D'Urso

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
    def __init__(self, parent, parent_process):
        self.main_window = parent
        self.parent_process = parent_process
        self.title = None
        super(TabHtmlWindow, self).__init__(parent, 'pythics.controls',
                                            multiprocessing.get_logger())
        # force widgets to redraw when the scrollbars are released
        #   this is needed for animated matplotlib widgets
        self.verticalScrollBar().sliderReleased.connect(self.redraw)
        self.horizontalScrollBar().sliderReleased.connect(self.redraw)

    def redraw(self):
        if not self.error:
            self.child_process.redraw()

    def close(self):
        if not self.error:
            try:
                self.parent_process.stop_child_process(self.child_process)
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
            self.child_process = self.parent_process.new_child_process(self.html_path, file_name_only, anonymous_controls, controls)
            self.child_process.start()
        except:
            message = 'Error while opening xml file %s\n' % file_name_only  + traceback.format_exc(0)
            QtWidgets.QMessageBox.critical(self, 'Error', message, QtWidgets.QMessageBox.Ok)
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
                                        self.child_process.default_parameter_filename)
                else:
                    if filename == '':
                        filename = self.main_window.get_open_filename('data (*.*)')
                    elif not os.path.isabs(filename):
                        filename = os.path.join(self.html_path, filename)
                if filename != '':
                    try:
                        self.child_process.load_parameters(filename)
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
                                        self.child_process.default_parameter_filename)
                else:
                    if filename == '':
                        filename = self.main_window.get_save_filename('data (*.*)')
                    elif not os.path.isabs(filename):
                        filename = os.path.join(self.html_path, filename)
                if filename != '':
                        self.child_process.save_parameters(filename)
            except:
                self.logger.exception('Error while loading parameters.')


class OptionsProcessor(object):
    def __init__(self):
        # configure the logger
        self.logger = multiprocessing.log_to_stderr()
        #self.logger.setLevel(logging.DEBUG)
        #self.logger.setLevel(logging.INFO)
        self.logger.setLevel(logging.WARNING)
        self.first_app = ""
        self.first_workspace = ""
        self.compact = False
        self.shutdown_on_exit = False

    def usage(self):
        print("""\
Usage: pythics-run.py [options]
Options:
  -h | --help       show help text then exit
  -a | --app        selects startup app
  -w | --workspace  selects startup workspace
  -c | --compact    run in compact mode with simplified controls for small screens
  -s | --shutdown   shutdown computer on exit (*nix only)
  -v | --verbose    selects verbose mode
  -d | --debug      selects debug mode""")

    def options(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'ha:w:csvd',
                                       ['help', 'app=', 'workspace=', 'compact', 'shutdown', 'verbose', 'debug'])
        except getopt.GetoptError as err:
            # print help information and exit:
            print(err) # will print something like "option -a not recognized"
            self.usage()
            sys.exit(2)
        for o, a in opts:
            if o in ('-v', '--verbose'):
                self.logger.setLevel(logging.INFO)
            elif o in ('-d', '--debug'):
                self.logger.setLevel(logging.DEBUG)
            elif o in ('-h', '--help'):
                self.usage()
                sys.exit(0)
            elif o in ('-a', '--app'):
                self.logger.info('opening app ' + a)
                self.first_app = a
            elif o in ('-w', '--workspace'):
                self.logger.info('opening workspace ' + a)
                self.first_workspace = a
            elif o in ('-s', '--shutdown'):
                self.logger.info('shutdown on exit')
                self.shutdown_on_exit = True
            elif o in ('-c', '--compact'):
                self.logger.info('compact mode')
                self.compact = True
            else:
                assert False, 'unhandled option'


#
# create and start the application
#
if __name__ == '__main__':
    manager = multiprocessing.Manager()
    application = QtWidgets.QApplication(sys.argv)
    parent_process = pythics.parent.Parent(manager)
    cl_options_processor = OptionsProcessor()
    cl_options_processor.options()
    window = MainWindow(parent_process, application, compact=cl_options_processor.compact)
    window.show()
    parent_process.start()
    if os.path.isfile(cl_options_processor.first_workspace):
        window.open_workspace(cl_options_processor.first_workspace)
    elif os.path.isfile(cl_options_processor.first_app):
        window.open_html_file(cl_options_processor.first_app)
    window.shutdown_on_exit = cl_options_processor.shutdown_on_exit
    application.exec_()

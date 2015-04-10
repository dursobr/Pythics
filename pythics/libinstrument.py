# -*- coding: utf-8 -*-
#
#  Copyright 2008 - 2013 Brian R. D'Urso
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
import visa


class GPIBInstrument(visa.GpibInstrument):
    def clear_status(self):
        self.write('*CLS')

    def reset(self):
        self.write('*RST')

    # identity property
    def __get_identity(self):
        return self.ask('*IDN?')

    identity = property(__get_identity)



## class VISAInstrument(wx.Panel, pythics.libcontrols.Control):
    ## @pythics.libcontrols.catch_exception
    ## def __init__(self, parent, key='', global_access=False,
                 ## label='',
                 ## *args, **kwargs):

        ## ## wx.StaticBox.__init__(self, parent, wx.ID_ANY, label=label,
                           ## ## **kwargs)
        ## ## self.box_sizer = wx.StaticBoxSizer(self, wx.VERTICAL)

        ## ## t = wx.StaticText(parent, -1, "Controls placed \"inside\" the box are really its siblings")
        ## ## self.box_sizer.Add(t, 0, wx.TOP|wx.LEFT, 10)

        ## wx.Panel.__init__(self, parent, wx.ID_ANY, *args, **kwargs)
        ## self.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        ## self.box = wx.StaticBox(self, wx.ID_ANY, label=label)
        ## self.panel_sizer.Add(self.box, proportion=0, flag=wx.EXPAND, border=0)
        ## self.SetSizer(self.panel_sizer)

        ## self.box_sizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)
        ## t = wx.StaticText(self, -1, "Controls placed \"inside\" the box are really its siblings")
        ## t2 = wx.StaticText(self, -1, "Another line of text")
        ## t3 = wx.StaticText(self, -1, "Another line of text")
        ## t4 = wx.StaticText(self, -1, "Another line of text")
        ## self.box_sizer.Add(t, proportion=0, flag=wx.TOP|wx.LEFT, border=5)
        ## self.box_sizer.Add(t2, proportion=0, flag=wx.TOP|wx.LEFT, border=5)
        ## self.box_sizer.Add(t3, proportion=0, flag=wx.TOP|wx.LEFT, border=5)
        ## self.box_sizer.Add(t4, proportion=0, flag=wx.TOP|wx.LEFT, border=5)
        ## self.box_sizer.Layout()
        ## self.box_sizer.SetSizeHints(self.box)

        ## self.panel_sizer.Layout()
        ## self.panel_sizer.SetSizeHints(self)
        ## pythics.libcontrols.Control.__init__(self, parent,
                                          ## action=None,
                                          ## key=key,
                                          ## save=False,
                                          ## global_access=global_access)

    ## def generate_proxy(self, return_queue):
        ## return VISAInstrumentProxy(self, return_queue)


## #
## # Proxy
## #
## class VISAInstrumentProxy(pythics.libcontrols.ControlProxy):
    ## @pythics.libcontrols.gui_call
    ## def trigger_action(self):
        ## self._control.run_action_no_event()

    ## # action property
    ## @pythics.libcontrols.gui_call
    ## def __get_action(self):
        ## return self._control.action

    ## @pythics.libcontrols.gui_call
    ## def __set_action(self, value):
        ## self._control.action = value

    ## action = property(__get_action, __set_action)

    ## # label property
    ## @pythics.libcontrols.gui_call
    ## def __get_label(self):
        ## return self._control.GetLabel()

    ## @pythics.libcontrols.gui_call
    ## def __set_label(self, value):
        ## self._control.SetLabel(value)

    ## label = property(__get_label, __set_label)

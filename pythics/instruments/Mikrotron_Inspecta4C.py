#
#  Copyright 2008, 2009 Brian R. D'Urso
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


#Interface class for Inspecta

from ctypes import *
inspecta_dll = windll.LoadLibrary("MVFGD32.DLL")

malloc = cdll.msvcrt.malloc
free = cdll.msvcrt.free
memcpy = cdll.msvcrt.memcpy

mvfg_open = inspecta_dll.mvfg_open
mvfg_close = inspecta_dll.mvfg_close
mvfg_getparam = inspecta_dll.mvfg_getparam
mvfg_setparam = inspecta_dll.mvfg_setparam
mvfg_errmessage = inspecta_dll.mvfg_errmessage
mvfg_grab = inspecta_dll.mvfg_grab
mvfg_getbufptr = inspecta_dll.mvfg_getbufptr

MVFG_OK = 0L

#global parameters for GetParam and SetParam
MVFGPAR_CAMMODE	= "CamMode"
MVFGPAR_LINELEN	= "LineLen"
MVFGPAR_NUMLIN = "NumLin"
MVFGPAR_BLACKLINESBEGIN = "BlackLinesBegin"
MVFGPAR_BLACKLINESEND = "BlackLinesEnd"
MVFGPAR_BLANKTIME = "BlankTime"
MVFGPAR_WHITELEVEL = "WhiteLevel"
MVFGPAR_BLACKLEVEL = "BlackLevel"
MVFGPAR_VIDEONORM = "Videonorm"
MVFGPAR_INTERLACED = "Interlaced"
MVFGPAR_REQFRAME = "ReqFrame"
MVFGPAR_CAMSEL = "CamSel"
MVFGPAR_DIGSEL = "DigSel"
MVFGPAR_PHOTO = "Photo"
MVFGPAR_PHOTOFLAG = "PhotoFlag"
MVFGPAR_SYNCSOURCE = "SyncSource"
MVFGPAR_SYNCLEVEL = "SyncLevel"
MVFGPAR_SCANPERIOD = "ScanPeriod"
MVFGPAR_SCANRATE = "ScanRate"			
MVFGPAR_EXPTIME = "ExpTime"			
MVFGPAR_LTFACTOR = "LT-Factor"
MVFGPAR_LTFACTORRED = "LT-FactorRed"
MVFGPAR_LTFACTORGREEN = "LT-FactorGreen"
MVFGPAR_LTFACTORBLUE = "LT-FactorBlue"
MVFGPAR_CONTINUOUSFLAG = "ContinuousFlag"
MVFGPAR_EXTPHOTOFLAG = "ExtPhotoFlag"	
MVFGPAR_TRIGGERMODE = "TriggerMode"		
MVFGPAR_CAPFRAME = "CapFrame"			
MVFGPAR_EXTTRIGGERFLAG = "ExtTriggerFlag"
MVFGPAR_EXTTRIGGEREDGE = "ExtTriggerEdge"
MVFGPAR_EXTRRIGGERMASK = "ExtTriggerMask"
MVFGPAR_TIMEOUT = "Timeout"	
MVFGPAR_FORMAT_INFO = "FormatInfo"	
MVFGPAR_ENCODERFLAG = "EncoderFlag"	
MVFGPAR_DIVIDER = "Divider"
MVFGPAR_ENAENC = "EnaEnc"
MVFGPAR_BUFFERMODE = "BufferMode"
MVFGPAR_CAMSTRING = "CamString"
MVFGPAR_UNIMODE = "GrabberConfData"	
MVFGPAR_VIDEOCLOCK = "Videoclock"
MVFGPAR_HORDIVIDER = "HorDivider"
MVFGPAR_CLKRECOVER = "ClkRecovery"

#parameter values for mvfg_grab (iCommand)							
GRAB_WAIT = 0
GRAB_NOWAIT = 1
GET_STATUS = 2
GET_STATUS_WAIT = 3


class Camera:

    def __init__(self):
        self.open = False

    def Open(self, device_number, pc_camera_profile):
        if self.open:
            raise Exception('camera is already open')
        else:
            self.device_number = device_number
            self.pc_camera_profile = pc_camera_profile
            mvfg_open.argtypes = [c_char_p, c_long] #specify argument types that mvfg_open can take
            err = mvfg_open(pc_camera_profile, self.device_number)
            if err != MVFG_OK:
                return mvfg_errmessage(err)    #display any error messages
            self.open = True

            class FORMAT_INFO(Structure):
                _fields_ = [("iNumberOfPlanes", c_int),
                            ("iChannelsPerPlane", c_int),
                            ("iBitsPerChannel", 8*c_int),
                            ("iOffsetNIOC", c_int),
                            ("lImageWidth", c_long),
                            ("lImageHeight", c_long),
                            ("lLineSize", c_long),
                            ("lPlaneSize", c_long),
                            ("lFrameSize", c_long),
                            ("lColorFormat", c_long)]

        
            malloc.restype = POINTER(FORMAT_INFO)
            sFormat = malloc(sizeof(FORMAT_INFO))
            err = mvfg_getparam(MVFGPAR_FORMAT_INFO, sFormat, 0)  
            if err != MVFG_OK:
               return mvfg_errmessage(err)    #display any error messages

            #create python dictionary to hold formatInfo information
            self.formatInfo = dict()
            self.formatInfo['NumberOfPlanes'] = sFormat.contents.iNumberOfPlanes
            self.formatInfo['ChannelsPerPlane'] = sFormat.contents.iChannelsPerPlane
            self.formatInfo['BitsPerChannel'] = sFormat.contents.iBitsPerChannel
            self.formatInfo['OffsetNIOC'] = sFormat.contents.iOffsetNIOC
            self.formatInfo['ImageWidth'] = sFormat.contents.lImageWidth
            self.formatInfo['ImageHeight'] = sFormat.contents.lImageHeight
            self.formatInfo['LineSize'] = sFormat.contents.lLineSize
            self.formatInfo['PlaneSize'] = sFormat.contents.lPlaneSize
            self.formatInfo['FrameSize'] = sFormat.contents.lFrameSize
            self.formatInfo['ColorFormat'] = sFormat.contents.lColorFormat

            free(sFormat)

    def SetParam(self, pc_param_name, pc_param_value):
        if self.open:
            mvfg_setparam.argtypes = [c_char_p, c_char_p, c_long]
            err = mvfg_setparam(pc_param_name, pc_param_value, self.device_number)
            return mvfg_errmessage(err)    #display any error messages
        else:
            raise Exception('camera is not open')

    def GetParam(self, pc_param_name):
        if self.open:
            p_value_buffer = c_buffer(sizeof(c_long))
            err = mvfg_getparam(pc_param_name, p_value_buffer, self.device_number)
            if err != MVFG_OK:
               return mvfg_errmessage(err)    #display any error messages
            return p_value_buffer
        else:
            raise Exception('camera is not open')

    def NewBuffer(self):
        if self.open:
            self.buf = c_buffer(sizeof(c_char)*(self.formatInfo['FrameSize'])) #create a "FrameSize"-byte buffer, initialized to NUL bytes
            return self.buf
        else:
            raise Exception('camera is not open')
    
    def GrabAndCopy(self):
        if self.open:
            err = mvfg_grab(GRAB_WAIT, self.device_number)
            memcpy(self.buf, mvfg_getbufptr(self.device_number), self.formatInfo['FrameSize'])
            return mvfg_errmessage(err)
        else:
            raise Exception('camera is not open')

    #def InitGrabNowait(self):
    #    err = mvfg_grab(GRAB_NOWAIT, self.device_number)
    #    return mvfg_errmessage(err)

    #def GrabAndCopyNowait(self):      
    #    err = mvfg_grab(GRAB_NOWAIT, self.device_number)
    #    if err != MVFG_OK:
    #       return mvfg_errmessage(err)
    #    while mvfg_grab(GET_STATUS, self.device_number):
    #        pass
    #    memcpy(self.buf, mvfg_getbufptr(self.device_number), self.formatInfo['FrameSize'])

    def Close(self):
        if self.open:
            mvfg_close.argtypes = [c_long]
            err = mvfg_close(self.device_number)
            self.open = False
            return mvfg_errmessage(err)    #display any error messages
        else:
            raise Exception('camera is not open')


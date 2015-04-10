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
#  Module by Elliot Jenner, updated 9/16/2013

import visa


class stepper_motor(visa.SerialInstrument):
    def __init__(self, loc, mode='Jog', vel_max = 10.0, accel_max=400.0):
        visa.SerialInstrument.__init__(self, loc)
        self.term_chars = visa.CR
        self.ask('PR4') #turn on acknowledgement
        self.write('IFD')
        self.accel_max = accel_max
        self.vel_max = vel_max
        self.is_moving = False
        self.__mode = mode
        
    def __return_parser(self, responce):
        #buffering issues sometimes occur where the ack-nak charter does not get pulled and waits for next read. Must clear to get to proper return if expecting value.
        if responce.partition('%')[1] != '%' or responce.partition('*')[1] != '*':
            return responce
        elif  responce.partition('?')[1] !='?':
            return self.__acknowledge(responce, True)
        else:
            return self.__return_parser(self.read())
    
    def __acknowledge(self, input, check = False):
    #return interpreter - for items that do not return numerical answers, a three symbol code is used.
        if input == ('%' or '*'): #% for instant, * for buffered
            return True
        else:# failure includes a code indicating failure type. to check, check = True
            if not check:
                return False
            else:
                error = {
                '1' : 'Timeout',
                '2' : 'Parameter Too Long',
                '3' : 'Too Few Parameters',
                '4' : 'Too Many Parameters',
                '5' : 'Parameter Out Of Range',
                '6' : 'Buffer Full',
                '7' : 'Cannot Process Command',
                '8' : 'Program Running',
                '9' : 'Bad Password',
                '10': 'Comm Port Error',
                '11': 'Bad Character',
                }
                return error[input.partition('%')[2]]
    
    #Process Commands - normal operation
    
    #motion commands
    def __get_mode(self):
        #mode defaults to Jog
        return self.__mode
        
    def __set_mode(self, mode):
        self.__mode = mode
        return True

    mode = property(__get_mode, __set_mode)
    
    def start(self):
        self.motor_enable()
        if self.mode == 'Jog':
            #accelerates with (accel) to speed set by (vel)
            stat = self.ask('CJ')
            if self.__acknowledge(stat):
                self.is_moving = True
        else:
            return 'wrong mode'
    
    def set_move(self, dist):
        self.motor_enable()
        #make a stepwise move
        if self.mode == 'Step':
            command = 'FL'+ str(dist)
            stat = self.__return_parser(self.ask(command))
            if self.__acknowledge(stat):
                self.is_moving = True
        else:
            return 'wrong mode'
            
    def set_position(self, pos):
        #set the current position to pos
        command = 'SP'+ str(pos)
        return self.ask(command)

    def stop(self):
        if self.mode == 'Jog':
            #stops jog at decel rate (set decell)
            stat = self.ask('SJ')
        elif self.mode == 'Step':
            #stops steped movement with rate from (set_deccel)
            stat =  self.ask('STD')
        if self.__acknowledge(stat):
            self.is_moving = False
    
    def __get_vel(self):
        if self.mode == 'Jog':
            #get currently set velocity in rev/sec. commands are different depending on if the motor is already moving.
            if self.is_moving:
                reply = self.__return_parser(self.ask('CS'))
            else:
                reply = self.__return_parser(self.ask('JS'))
        elif self.mode == 'Step':
            #get currently set velocity in rev/sec
            reply = self.__return_parser(self.ask('VE'))
        elif self.mode == 'Analog':
            return self.vel_max
        try:
            return float(reply.partition('=')[2])
        except ValueError:
            return reply
       
    def __set_vel(self, vel):
        vel = '%.4f' % vel
        if self.mode == 'Jog':
            #set velocity in rev/sec. commands are different depending on if the motor is already moving. Be sure to set before start or last value set when motor is not moving has prescednece.
            if self.is_moving:
                command = 'CS' + str(vel)
            else:
                if float(vel) < 0:
                    self.ask('DI-1') #set this to go counter clockwise
                    vel[1:] #pull off the negative sign, this command doesn't understand it
                else:
                    self.ask('DI1') #set this to go clockwise
                command = 'JS'+ str(vel)
        elif self.mode == 'Step':
            #set velocity in rev/sec
            if self.is_moving:
                command = 'VC'+ str(vel)
            else:
                command = 'VE'+ str(vel)
        return self.ask(command)

    vel = property(__get_vel, __set_vel)
    
    def get_current_vel(self): #returns the actual current velocity, rather than the set volocity as vel does. Replies in RPM, not RPS
        if self.mode == 'Jog':
            #get currently set velocity in rev/min. commands are different depending on if the motor is already moving.
            reply = self.__return_parser(self.ask('RLJ')) #Checks the intermediate commands. It does not read back anything from the motor  
            if 'RS' in reply: #buffering catch
                reply = self.read()
        elif self.mode == 'Step':
            #get currently set velocity in rev/min
            reply = self.__return_parser(self.ask('RLJ')) #Checks the intermediate commands. It does not read back anything from the motor
            if 'RS' in reply: #buffering catch
                reply = self.read()
        elif self.mode == 'Analog':
            return self.vel_max
        try:
            return float(reply.partition('=')[2])*0.25
        except ValueError:
            return reply*0.25
        
    def __get_accel(self):
        if self.mode == 'Jog':
            #get currently set Acceleration in rev/sec/sec. 
            reply = self.__return_parser(self.ask('JA'))
        elif self.mode == 'Step':
            #get currently set Acceleration in rev/sec/sec
            reply = self.__return_parser(self.ask('AC'))
        elif self.mode == 'Analog':
            return self.accel_max
        try:
            return float(reply.partition('=')[2])
        except ValueError:
            return reply
       
    def __set_accel(self, accel): 
        accel += 0.01 #due to truncation issues, it is necesary to increase the last digit
        accel = '%.4f' % accel
        if self.mode == 'Jog':
            #set acceleration in rev/sec/sec CANNOT BE CHANGED WHILE MOVING
            command = 'JA'+ str(accel)
        elif self.mode == 'Step':
            #set acceleration in rev/sec/sec
            command = 'AC'+ str(accel)
        return self.ask(command)

    accel = property(__get_accel, __set_accel)
    
    def __get_dccel(self):
        if self.mode == 'Jog':
            #get currently set Decceleration in rev/sec/sec
            reply =  self.__return_parser(self.ask('JL'))
        elif self.mode == 'Step':
            #get currently set Decceleration in rev/sec/sec
            reply = self.__return_parser(self.ask('DE'))
        elif self.mode == 'Analog':
            return self.accel_max
        try:
            return float(reply.partition('=')[2])
        except ValueError:
            return reply
       
    def __set_dccel(self, dccel):
        dccel += 0.01 #due to truncation issues, it is necesary to increase the last digit
        dccel = '%.4f' % dccel
        if self.mode == 'Jog':
            #set decceleration in rev/sec/sec. CANNOT BE CHANGED WHILE MOVING
            command = 'JL'+ str(dccel)
        elif self.mode == 'Step':
            #set decceleration in rev/sec/sec
            command = 'DE'+ str(dccel)
        elif self.mode == 'Analog':
            return 0
        return self.ask(command)

    dccel = property(__get_dccel, __set_dccel)   
    
    # analog commands
    def motor_mode_set(self,offset = 0.0, max_voltage = 5.0, deadband = 0.0): #NOTE deadband set in mV, all others in V
        if self.mode == 'Analog Velocity':
            self.motor_disable()
            self.ask('CM11') #go to analog velocity mode
            self.deadband = deadband
            self.scaling = 'Single Ended 0-5' #to match the capability of the ST5-S
            self.offset = offset
            self.max_voltage = max_voltage
        elif self.mode == 'Analog Position':
            self.motor_disable()
            self.ask('CM22') #go to analog position mode
            self.deadband = deadband
            self.scaling = 'Single Ended 0-5' #to match the capability of the ST5-S
            self.offset = offset
            self.max_voltage = max_voltage
        elif self.mode == 'Jog' or self.mode == 'Step':
            self.ask('CM21') #normal mode
            self.motor_enable()
        return True
        
    def __get_pos_gain(self): #the position in degrees given by the maximum analog input
        if self.mode == 'Analog Position':
            setting = self.__return_parser(self.ask('AP'))
            setting = float(setting.partition('=')[2])
            return (setting*(360.0/20000.0))
        else:
            return 'wrong mode'
    
    def __set_pos_gain(self, pos):
        if self.mode == 'Analog Position':
            input = int(pos*(20000.0/360.0))#convert from degrees to encoder counts where 1rev = 20000 counts
            return self.ask('AP' + str(input)) 
        else:
            return 'wrong mode'
            
    pos_gain = property(__get_pos_gain, __set_pos_gain)    
            
    def __get_vel_gain(self): #the speed given by the maximum analog input in RPS. 
        if self.mode == 'Analog Velocity':
            setting = self.__return_parser(self.ask('AG'))
            setting = float(setting.partition('=')[2])
            return (setting/240.0)/(4.0*self.max_voltage/(self.max_voltage-self.offset))
        else:
            return 'wrong mode'
    
    def __set_vel_gain(self, vel):
        if self.mode == 'Analog Velocity':
            vel = 4.0*vel*(self.max_voltage/(self.max_voltage-self.offset))#compensates for offsets by comparing the offset to the maximum input voltage so the the highest point off center of the input wave will be the full set velocity
            input = int(vel*240.0)#240*speed in RPS gives the motor setting to match
            return self.ask('AG' + str(input)) 
        else:
            return 'wrong mode'
            
    vel_gain = property(__get_vel_gain, __set_vel_gain)    
        
    def __get_accel_max(self):
        #get currently set maximum allowed Acceleration in rev/sec/sec. also max deceleration. Can be used in other modes. Also sets e-stop.
        reply = self.__return_parser(self.ask('AM'))
        try:
            return float(reply.partition('=')[2])
        except ValueError:
            return reply
       
    def __set_accel_max(self, accel):
        #set maximum allowed acceleration in rev/sec/sec. also sets max deceleration. Can be used in other modes. Also sets e-stop.
        accel += 0.01 #due to truncation issues, it is necesary to increase the last digit
        accel = '%.2f' % accel
        command = 'AM'+ str(accel)
        return self.ask(command)

    accel_max = property(__get_accel_max, __set_accel_max)
    
    def __get_offset(self): #offset for analog input in Volts. this value is read as zero
        if self.mode == 'Analog Position' or self.mode == 'Analog Velocity':
            reply = self.ask('AV')
            return float(reply.partition('=')[2])
        else:
            return 'wrong mode'
    
    def __set_offset(self, voltage = 0.0):
        if self.mode == 'Analog Position' or self.mode == 'Analog Velocity':
            if voltage == 'seek':
                return self.ask('AZ') #pulls the current value of the voltage and sets it as the zero input
            else:
                return self.ask('AV' + str(voltage)) #set to the designated value
        else:
            return 'wrong mode'
            
    offset= property(__get_offset, __set_offset)    
    
    def __get_filter(self): #analog input frequency filter in Hz. a value of zero indicates the filter is disabled
        if self.mode == 'Analog Position' or self.mode == 'Analog Velocity':
            input = self.ask('AF')
            input = float(input.partition('=')[2])
            if input == 0:
                return 0
            else:
                frequency = 1400/((72090/input) - 2.2)
                return frequency
        else:
            return 'wrong mode'
    
    def __set_filter(self, frequency = 0.0):
        if self.mode == 'Analog Position' or self.mode == 'Analog Velocity':
            if frequency != 0:
                input = int(72090/((1400/frequency)+2.2))
            else:
                input = 0
            return self.ask('AF' + str(input))
        else:
            return 'wrong mode'
            
    filter = property(__get_filter, __set_filter)     
    
    def __get_deadband(self): #deadband is the magnitude of the voltage (in mV) around the zero setpoint (both ways) the will be interpreted as zero
        if self.mode == 'Analog Position' or self.mode == 'Analog Velocity':
            reply = self.ask('AD')
            return float(reply.partition('=')[2])
        else:
            return 'wrong mode'
    
    def __set_deadband(self, voltage):
        if self.mode == 'Analog Position' or self.mode == 'Analog Velocity':
            return self.ask('AD' + str(voltage))
        else:
            return 'wrong mode'
            
    deadband = property(__get_deadband, __set_deadband)    
    
    def __get_scaling(self): #sets the input type the motor is expecting.
        if self.mode == 'Analog Position' or self.mode == 'Analog Velocity':
            setting = self.ask('AS')
            setting = float(setting.partition('=')[2])
            if setting == 0: return 'Single Ended +-10'
            elif setting == 1: return 'Single Ended 0-10'
            elif setting == 2: return 'Single Ended +-5'
            elif setting == 3: return 'Single Ended 0-5'
            elif setting == 4: return 'Double Ended +-10'
            elif setting == 5: return 'Double Ended 0-10'
            elif setting == 6: return 'Double Ended +-5'
            elif setting == 7: return 'Double Ended 0-5'
        else:
            return 'wrong mode'
    
    def __set_scaling(self, setting):
        if self.mode == 'Analog Position' or self.mode == 'Analog Velocity':
            if setting == 'Single Ended +-10': input = 0
            elif setting == 'Single Ended 0-10': input = 1
            elif setting == 'Single Ended +-5': input = 2
            elif setting == 'Single Ended 0-5': input = 3
            elif setting == 'Double Ended +-10': input = 4
            elif setting == 'Double Ended 0-10': input = 5
            elif setting == 'Double Ended +-5': input = 6
            elif setting == 'Double Ended 0-5': input = 7
            return self.ask('AG' + str(input))
        else:
            return 'wrong mode'
            
    scaling = property(__get_scaling, __set_scaling)   
    #auxiliary commands
    
    def wait(self, time):
        #pauses execution of commands for time seconds (0.0-320s with 0.01 resolution). NOTE:ONLY ESTOP OVERRIDES! OTHER STOP COMMANDS WILL WAIT!
        command = 'WT'+ str(time)
        return self.ask(command)  
        
    def monitor_string(self, string):
        #the motor will send this string back when this command is reached (for monitoring delays)
        self.write('SS' + str(string))
        return self.read()
       
    #Setup Commands - These commands are normally set beforehand and left alone. Can be place in non-volitile momory in controller using save
    def save(self):
        return self.ask('SA')
    
    def motor_enable(self):
        #enable motor at start of use, after motor_disable, or after alarm has shut it down.
        return self.ask('ME')
        
    def motor_disable(self):
        #disables the motor. call motor enable to reactive
        return self.ask('MD')
    
    #emergency commands
    def e_brake(self):
        #stops all motion at maximum allowed acceleration (set by set_accel_max). Clears any unexecuted commands from buffer.
        stat = self.ask('SK')
        self.vel_gain = 0
        if self.__acknowledge(stat):
            self.is_moving = False
        return stat
        
    def reset(self):
        #resets drive to startup parameters and leaves it in motor disabled. For accident recovery
        return self.ask('RE')
        
    @property
    def status(self):
        #check machine status
        status = self.ask('RS')
        status = status.partition('=')[2]
        status = list(status)
        states = {
        'A' : 'Alarm',
        'D' : 'Disabled',
        'E' : 'Drive Fault',
        'F' : 'Motor Moving',
        'H' : 'Homing',
        'J' : 'Jogging',
        'M' : 'Motion in progress',
        'P' : 'In position',
        'R' : 'Ready',
        'S' : 'Stopping a motion',
        'T' : 'Wait Time',
        'W' : 'Wait Input',
        }
        output = ''
        for i in status:
            if i.isdigit() or i == '.':
                continue
            else:
                state = states[i]
                if state == 'Alarm':
                    state += ':' + alarm
                output +=  state + ', '
        return output
    
    @property
    def alarm(self):
        #get alarm code. returns hex code if ret = hex or error string if ret = str. use alarm reset to clear
        error = self.ask('AL')
        error = error.partition('=')[2] #returns AL=HexCode, so dump off the string part of the return
        message = {
        '0000' : 'No Alarm',
        '0001' : 'Position Limit',
        '0002' : 'CCW Limit',
        '0004' : 'CW Limit',
        '0008' : 'Over Temp',
        '0010' : 'Internal Voltage',
        '0020' : 'Over Voltage',
        '0040' : 'Under Voltage',
        '0080' : 'Over Current',
        '0100' : 'Open Motor Winding',
        '0200' : 'Bad Encoder',
        '0400' : 'Comm Error',
        '0800' : 'Bad Flash',
        '1000' : 'No Move',
        '4000' : 'Blank Q Segment',
        }
        error = message[error]
        if error != 'Comm Error':
            return error
        else:
            return 'Comm Error:' + comm_error
        
    def alarm_reset(self):
        #resets alarm codes. if alarms are clear, Does not clear motor shutdown, use motor_enable.
        error = self.ask('AR')        
        error = error.partition('=')[2] #returns AL=HexCode, so dump off the string part of the return
        if error == '':
            error = '0000'
        message = {
        '0000' : 'No Alarm',
        '0001' : 'Position Limit',
        '0002' : 'CCW Limit',
        '0004' : 'CW Limit',
        '0008' : 'Over Temp',
        '0010' : 'Internal Voltage',
        '0020' : 'Over Voltage',
        '0040' : 'Under Voltage',
        '0080' : 'Over Current',
        '0100' : 'Open Motor Winding',
        '0200' : 'Bad Encoder',
        '0400' : 'Comm Error',
        '0800' : 'Bad Flash',
        '1000' : 'No Move',
        '4000' : 'Blank Q Segment',
        }
        error = message[error]
        if error != 'Comm Error':
            return 'Alarm:' + error
        else:
            return 'Comm Error:' + comm_error

    @property
    def comm_error(self):
        #communication errors have there own syntax and output
        code = self.ask('CE')
        code = code.partition('=')[2]
        problem = {
        '0000' : 'No Error',
        '0001' : 'parity flag error',
        '0002' : 'framing error',
        '0004' : 'noise flag error',
        '0008' : 'overrun error',
        '0010' : 'Rx buffer full',
        '0020' : 'Tx buffer full',
        '0040' : 'bad SPI op-code',
        '0080' : 'Tx time-out',
        }
        return problem[code]

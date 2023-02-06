# -*- coding: utf-8 -*-
# 4tronix M.A.R.S. Rover Robot remote control using the PiHut Wireless USB Game Controller
#
#  Copyright 2023 Istvan Z. Kovacs. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Implements the custom remote drive functions """

from time import sleep
from math import atan2, pi

# Local
from approxeng.input.selectbinder import ControllerResource
from drivelogger import driveLogger
from driveconfig import driveCfg

# Default/initial rover speed and movement direction
SPEED = 20
DIR   = 0

### Joystick controlls mixers functions
def mixerSpeed(yaw: float=0.0, throttle: float=0.0, max_power: int=100) -> tuple[int, int]:
    """
    Mix a pair of controller axes, returning a pair of wheel speeds. 
    This is where the mapping from controller positions to wheel powers is defined.
    
    :param yaw: 
        Yaw axis value, ranges from -1.0 to 1.0
    :param throttle: 
        Throttle axis value, ranges from -1.0 to 1.0
    :param max_power: 
        Maximum speed that should be returned from the mixer, defaults to 100
    :return: 
        When yaw <> 0: a pair of power_left, power_right integer values to send to the left and right motor drivers
        Else: a single power integer value to send to both motor drivers
    """
    if yaw == 0:
        scale = float(max_power) / max(1, abs(throttle))
        return int(throttle* scale), 0
    else:
        left  = throttle + yaw
        right = throttle - yaw
        scale = float(max_power) / max(1, abs(left), abs(right))
        return int(left * scale), int(right * scale)

def mixerDir(lr: float=0.0, fb: float=0.0, max_dir: float=30.0)-> int:
    """
    Mix a pair of controller axes, returning a direction/angle. 
    This is where the mapping from controller positions to wheel direction is defined.
    
    :param lr: 
        Left-right axis value, ranges from -1.0 to +1.0
    :param fb: 
        Fwd-back axis value, ranges from -1.0 to +1.0
    :param max_dir: 
        Maximum direction that should be returned from the mixer, defaults to 80 (degrees)
    :return: 
        A direction integer value to send to the motor drivers
    """
    angle_deg = (180/pi)*atan2(lr, abs(fb))
    #print(f"angle_deg={angle_deg}")
    if angle_deg >= 0:
        return int(min(max_dir, angle_deg))
    else:
        return int(max(-max_dir, angle_deg))

### Force-feedback functions
def rumbleStart(wugc: ControllerResource = None) -> None:
    """
    Activate force-feedback.
    Rumble tow times shortly.
    
    :param wugc: 
        approxeng.input.selectbinder.ControllerResource
    """
    if wugc is not None and driveCfg.FF_DEVICE is not None:
        wugc.ff_device = driveCfg.FF_DEVICE
        wugc.rumble(500)
        sleep(0.5)
        wugc.rumble(500)
        sleep(0.5)

def rumbleEnd(wugc: ControllerResource = None) -> None:
    """
    Activate force-feedback.
    Rumble tow times shortly.
    
    :param wugc: 
        approxeng.input.selectbinder.ControllerResource
    """
    if wugc is not None and driveCfg.FF_DEVICE is not None:
        wugc.rumble()
        sleep(0.5)
        wugc.rumble()
        sleep(0.5)

### LED effects
def flashAllLED(fnum: int=3, dly: float=0.5, col: int=0) -> None:
    """
    Flash all LEDs simultanously.
    
    :param fnum: 
        Number of flashes
    :param dly: 
        Delay in seconds between flashes
    :param col: 
        LED light color to use
    """
    if driveCfg.LED_NUM > 0:
        for f in range(fnum):
            rover.clear()
            rover.setColor(col)
            rover.show()
            sleep(dly)
        rover.clear()

def seqAllLED(fnum: int=3, dly: float=0.5, col: int=0) -> None:
    """
    Flash all LEDs in sequence.
    
    :param fnum: 
        Number of flashes
    :param dly: 
        Delay in seconds between flashes/LEDs
    :param col: 
        LED light color to use
    """
    if driveCfg.LED_NUM > 0:
        for f in range(fnum):
            for l in range(driveCfg.LED_NUM):
                rover.clear()
                rover.setPixel(l, col)
                rover.show()
                sleep(dly)
        rover.clear()

def flashLED(led: int=0, fnum: int=3, dly: float=0.5, col1: int=driveCfg.LED_BLACK, col2: int=driveCfg.LED_WHITE) -> None:
    """
    Flash a LED between two colors.

    :param led: 
        LED number, ranges from 0 to driveCfg.LED_NUM-1
    :param fnum: 
        Number of flashes
    :param dly: 
        Delay in seconds between flashes/LEDs
    :param col1: 
        First LED light color to use
    :param col2: 
        Second LED light color to use
    """
    if driveCfg.LED_NUM > 0 and led >=0 and led < driveCfg.LED_NUM:
        for f in range(fnum):
            rover.setPixel(led, col1)
            rover.show()
            sleep(dly)
            rover.setPixel(led, col2)
            rover.show()
            sleep(dly)


def setRLFBLED(fwd: bool=True, dir: int=0) -> None:
    """
    Set forward-back and left-right LED.
    
    :param fwd: 
        Movement forward (True) or reverse (False)
    :param dir: 
        Movement right (>0) or straight (=0) or left (<0)
    """
    if driveCfg.LED_NUM > 0:
        if fwd:
            # Set forward-back LEDs
            if dir > 0: # right
                rover.setPixel(1, driveCfg.LED_WHITE_H)
                rover.setPixel(2, driveCfg.LED_WHITE)

                flashLED(3, 1, 0.2, driveCfg.LED_RED, driveCfg.LED_RED_H)

            elif dir < 0: # left
                rover.setPixel(1, driveCfg.LED_WHITE)
                rover.setPixel(2, driveCfg.LED_WHITE_H)

                flashLED(0, 1, 0.2, driveCfg.LED_RED, driveCfg.LED_RED_H)

            else:
                rover.setPixel(1, driveCfg.LED_WHITE_H)
                rover.setPixel(2, driveCfg.LED_WHITE_H)

            # Set back LEDs
            rover.setPixel(0, driveCfg.LED_RED_H)
            rover.setPixel(3, driveCfg.LED_RED_H)

        else:
            # Set back LEDs
            if dir > 0: # right
                rover.setPixel(0, driveCfg.LED_RED_H)

                flashLED(3, 1, 0.2, driveCfg.LED_RED, driveCfg.LED_RED_H)

            elif dir < 0: # left
                rover.setPixel(3, driveCfg.LED_RED_H)

                flashLED(0, 1, 0.2, driveCfg.LED_RED, driveCfg.LED_RED_H)

            else:
                rover.setPixel(0, driveCfg.LED_RED_H)
                rover.setPixel(3, driveCfg.LED_RED_H)

            # Set forward LEDs
            rover.setPixel(1, driveCfg.LED_WHITE_H)
            rover.setPixel(2, driveCfg.LED_WHITE_H)

        rover.show()



### Attempt to import and initialise rover library
try:
    import rover

    def initRover(led_brightness: int=0) -> None:
        """
        As we have a rover library, initialise it.
        
        :param led_brightness: 
            LEDs default brightness, rnages from 0 to 100
        :return: 
            String with intialisation message
        """
        if driveCfg.LED_NUM > 0:
            # Init rover with initial LED brightness
            rover.init(led_brightness)    
            # Set all LED to green
            flashAllLED(3, 0.5, driveCfg.LED_GREEN)
            flashAllLED(1, 0.1, driveCfg.LED_GREEN_H)
        else:
            # No LEDs
            rover.init(0)

        driveLogger.debug("Rover initialisation. LED brightness = %d", led_brightness) 
        info_str = 'M.A.R.S. Rover library available.'
        driveLogger.info(info_str)
        driveCfg.journal_send(info_str)

    def moveRover(dir: float=DIR, speed: int=SPEED) -> None:
        """
        As we have a rover library, we can use the motors.
        Set simple rover movement: direction (left or right) and speed (forward or reverse).
        All motors set to the same speed.

        :param dir: 
            Direction angle value, ranges from -90.0 to +90.0
            A None value keeps unchnaged the current direction
        :param speed: 
            Speed value, ranges from -100 to 100
            A None value keeps unchnaged the current speed
        """
        if dir is not None:
            rover.setServo(driveCfg.SERVO_FL, dir)
            rover.setServo(driveCfg.SERVO_FR, dir)
            rover.setServo(driveCfg.SERVO_RL, -1*dir)
            rover.setServo(driveCfg.SERVO_RR, -1*dir)
            driveLogger.debug(f"Direction={dir}")

        if speed == 0:
            # Coast to stop
            rover.stop()

            # Set all LED to red
            flashAllLED(1, 0.1, driveCfg.LED_RED_H)

        elif speed > 0:
            # Move forward
            rover.forward(abs(speed))

            # Set forward-back left-right LED
            setRLFBLED(True, dir)

        elif speed < 0:
            # Move backward
            rover.reverse(abs(speed))

            # Set forward-back left-right LED
            setRLFBLED(False, dir)

        driveLogger.debug(f"Speed={speed}")
            
    def stopRover() -> None:
        """
        As we have a rover library, coast to stop.
        """

        # Stop rover
        rover.stop()

        # Flash 3 times all LEDs in red
        flashAllLED(3, 0.5, driveCfg.LED_RED)

        driveLogger.debug('Motors coast to stop!')

    def brakeRover() -> None:
        """
        As we have a rover library, brake and stop quickly.
        """
        rover.brake()
        rover.setServo(driveCfg.SERVO_FL, 0)
        rover.setServo(driveCfg.SERVO_FR, 0)
        rover.setServo(driveCfg.SERVO_RL, 0)
        rover.setServo(driveCfg.SERVO_RR, 0)

        # Flash 3 times all LEDs in red
        flashAllLED(3, 1, driveCfg.LED_RED)

        driveLogger.debug('Motors stop quickly!')

    def cleanupRover() -> None:
        """
        As we have a rover library, cleanup.
        """
        # Rotating LED lights
        seqAllLED(5, 0.1, driveCfg.LED_RED) 

        # Clean exit
        rover.cleanup()

        driveLogger.debug('Rover cleanup!')


# No rover libary
except ImportError:

    def initRover(led_brightness: int=0) -> str:
        """
        No rover libary - do nothing.

        :param led_brightness: 
            LEDs default brightness, rnages from 0 to 100
        :return: 
            String with intialisation message
        """
        driveLogger.debug('Dummy: Rover initialisation!') 
        warn_str = 'M.A.R.S. Rover library is NOT available, using dummy functions!'
        driveLogger.warning(warn_str)
        return warn_str

    def moveRover(dir: float=DIR, speed: int=SPEED) -> None:
        """
        No rover libary - print what we would have sent to it if we'd had one.

        :param dir: 
            Direction angle value, ranges from -90.0 to +90.0
            A None value keeps unchnaged the current direction
        :param speed: 
            Speed value, ranges from -100 to 100
            A None value keeps unchnaged the current speed
        """
        driveLogger.debug(f"Dummy: Direction={dir}")
        driveLogger.debug(f"Dummy: Speed={speed}")
        sleep(0.1)

    def stopRover() -> None:
        """
         No rover libary - do nothing.
        """
        rover.stop()
        driveLogger.debug('Dummy: Motors coast to stop!')

    def brakeRover() -> None:
        """
        No rover libary - do nothing.
        """
        driveLogger.debug('Dummy: Motors stop quickly!')

    def cleanupRover() -> None:
        """
        No rover libary - do nothing.
        """
        driveLogger.debug('Dummy: rover.cleanup()')


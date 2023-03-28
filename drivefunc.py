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

# pylint: disable=line-too-long

from time import sleep
from math import tan, atan2, pi, sqrt

# Local
from approxeng.input.selectbinder import ControllerResource
from drivelogger import driveLogger
from driveconfig import driveCfg

# Default/initial rover speed and movement direction
SPEED = 20
DIR = 0

# The last direction used
#prev_dir = 0

# Joystick controlls mixers functions


def mixer_speed(yaw: float = 0.0, throttle: float = 0.0, max_speed: int = 100) -> tuple[float, float]:
    """
    Mix a pair of controller axes, returning a pair of wheel speeds. 
    This is where the mapping from controller positions to wheel powers is defined.

    :param yaw: 
        Yaw axis value, ranges from -1.0 to 1.0
    :param throttle: 
        Throttle axis value, ranges from -1.0 to 1.0
    :param max_speed: 
        Maximum speed that should be returned from the mixer
        defaults to 100.0 (percentage of max speed)
    :return: 
        When yaw <> 0: a pair of power_left, power_right values 
        to send to the left and right motor drivers
        Else: a single power  value to send to both motor drivers
    """
    if yaw == 0.0:
        scale = float(max_speed) / max(1, abs(throttle))
        return throttle * scale, 0

    left = throttle + yaw
    right = throttle - yaw
    scale = float(max_speed) / max(1, abs(left), abs(right))
    return left * scale, right * scale


def mixer_dir(l_r: float = 0.0, f_b: float = 0.0, max_dir: float = 45.0) -> float:
    """
    Mix a pair of controller axes, returning a direction/angle. 
    This is where the mapping from controller positions to wheel direction is defined.

    :param l_r: 
        Left-right axis value, ranges from -1.0 to +1.0
    :param f_b: 
        Fwd-back axis value, ranges from -1.0 to +1.0
    :param max_dir: 
        Maximum direction that should be returned from the mixer
        defaults to 45 (degrees)
    :return: 
        A direction value to send to the motor drivers (degrees)
    """
    angle_rel = (2/pi)*atan2(l_r, abs(f_b))
    scale = float(max_dir) / max(1, abs(angle_rel))
    # print(f"angle_deg={angle_rel*90}")
    return angle_rel * scale


def calc_ackerman_steering(dir_deg: float = DIR, speed_per: float = SPEED) -> tuple[int, int, int, int]:
    """
    Calculate Ackerman rover steering.
    Left and Right motors can be set to different speeds and angles 
    according to Ackerman steering geometry. 
    See https://www.mathworks.com/help/sm/ug/mars_rover.html
    NOTE: Due to the 4tronix circuit design of the Main Board 
    all three wheels on the same side of the rover are set to the same speed!

    The max steering angle is limited to the value allowed by the rover chassis width
    i.e. the turn radius must be larger than the half of the chassis width (D).
    We choose to limit the minimum turn radius to 0.6 of the chassis width, 
    i.e. a bicycle steering angle of max atan2(L/2, 0.6*D) = 38.73 deg
    This limits to max 78.26 deg the (higher) angle of the inner wheels

    :param dir_deg: 
        Direction angle value (bicycle steering angle of the rover)
        ranges from -90.0 to +90.0 (degrees)
    :param speed_per: 
        Speed value (chassis speed of the rover)
        ranges from -100.0 to 100.0 (percentage of max speed)
    :return:
        A tuple with calculated dir_left, dir_right, speed_left, speed_right
    """
    dir_rad = (pi/180.0) * dir_deg
    if dir_deg != 0.0:
        dir_rad = min(abs(dir_rad), atan2(1.0, 1.2*driveCfg.DoL))
        dir_up_scale = atan2(1.0, (1.0/tan(dir_rad) - driveCfg.DoL))
        dir_down_scale = atan2(1.0, (1.0/tan(dir_rad) + driveCfg.DoL))

    # Limit the (higher) speed of the outer wheels to 100 (=max PWM duty cycle value, see rover.py)
    speed_up_scale = 1.0
    speed_down_scale = 1.0
    if speed_per != 0.0:
        speed_up_scale = sqrt(
            tan(dir_rad)**2 + (1 + driveCfg.DoL*tan(dir_rad))**2)
        speed_down_scale = sqrt(
            tan(dir_rad)**2 + (1 - driveCfg.DoL*tan(dir_rad))**2)
        if speed_up_scale > 100/speed_per:
            speed_per = 100/speed_up_scale

    if dir_deg > 0:
        dir_left = int((180.0/pi) * dir_down_scale)
        dir_right = int((180.0/pi) * dir_up_scale)
        speed_left = int(speed_per * speed_up_scale)
        speed_right = int(speed_per * speed_down_scale)
    elif dir_deg < 0:
        dir_left = int((-180.0/pi) * dir_up_scale)
        dir_right = int((-180.0/pi) * dir_down_scale)
        speed_left = int(speed_per * speed_down_scale)
        speed_right = int(speed_per * speed_up_scale)
    else:
        dir_left = 0
        dir_right = 0
        speed_left = speed_per
        speed_right = speed_per

    return dir_left, dir_right, speed_left, speed_right

# Force-feedback functions


def rumble_start(wugc: ControllerResource = None) -> None:
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


def rumble_end(wugc: ControllerResource = None) -> None:
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

# LED effects


def flash_all_leds(fnum: int = 3, dly: float = 0.5, col: int = 0) -> None:
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
        for _ in range(fnum):
            rover.clear()
            rover.setColor(col)
            rover.show()
            sleep(dly)
        rover.clear()


def seq_all_leds(fnum: int = 3, dly: float = 0.5, col: int = 0) -> None:
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
        for _ in range(fnum):
            for _l in range(driveCfg.LED_NUM):
                rover.clear()
                rover.setPixel(_l, col)
                rover.show()
                sleep(dly)
        rover.clear()


def flash_led(led: int = 0, fnum: int = 3, dly: float = 0.5, col1: int = driveCfg.LED_BLACK, col2: int = driveCfg.LED_WHITE) -> None:
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
    if driveCfg.LED_NUM > 0 and led >= 0 and led < driveCfg.LED_NUM:
        for _ in range(fnum):
            rover.setPixel(led, col1)
            rover.show()
            sleep(dly)
            rover.setPixel(led, col2)
            rover.show()
            sleep(dly)


def set_rlfb_led(fwd: bool = True, dir_deg: float = 0.0) -> None:
    """
    Set forward-back and left-right LED.

    :param fwd: 
        Movement forward (True) or reverse (False)
    :param dir_deg: 
        Movement right (>0) or straight (=0) or left (<0)
    """
    if driveCfg.LED_NUM > 0:
        if fwd:
            # Set forward-back LEDs
            if dir_deg > 0:  # right
                rover.setPixel(1, driveCfg.LED_WHITE_H)
                rover.setPixel(2, driveCfg.LED_WHITE)

                flash_led(3, 1, 0.2, driveCfg.LED_RED, driveCfg.LED_RED_H)

            elif dir_deg < 0:  # left
                rover.setPixel(1, driveCfg.LED_WHITE)
                rover.setPixel(2, driveCfg.LED_WHITE_H)

                flash_led(0, 1, 0.2, driveCfg.LED_RED, driveCfg.LED_RED_H)

            else:
                rover.setPixel(1, driveCfg.LED_WHITE_H)
                rover.setPixel(2, driveCfg.LED_WHITE_H)

            # Set back LEDs
            rover.setPixel(0, driveCfg.LED_RED_H)
            rover.setPixel(3, driveCfg.LED_RED_H)

        else:
            # Set back LEDs
            if dir_deg > 0:  # right
                rover.setPixel(0, driveCfg.LED_RED_H)

                flash_led(3, 1, 0.2, driveCfg.LED_RED, driveCfg.LED_RED_H)

            elif dir_deg < 0:  # left
                rover.setPixel(3, driveCfg.LED_RED_H)

                flash_led(0, 1, 0.2, driveCfg.LED_RED, driveCfg.LED_RED_H)

            else:
                rover.setPixel(0, driveCfg.LED_RED_H)
                rover.setPixel(3, driveCfg.LED_RED_H)

            # Set forward LEDs
            rover.setPixel(1, driveCfg.LED_WHITE_H)
            rover.setPixel(2, driveCfg.LED_WHITE_H)

        rover.show()


# Attempt to import and initialise rover library
try:
    import rover

    def init_rover(led_brightness: int = 0) -> None:
        """
        Initialise rover library.

        :param led_brightness: 
            LEDs default brightness, rnages from 0 to 100
        :return: 
            String with intialisation message
        """
        if driveCfg.LED_NUM > 0:
            # Init rover with initial LED brightness
            rover.init(led_brightness)
            # Set all LED to green
            flash_all_leds(3, 0.5, driveCfg.LED_GREEN)
            flash_all_leds(1, 0.1, driveCfg.LED_GREEN_H)
        else:
            # No LEDs
            rover.init(0)

        driveLogger.debug(
            "Rover initialisation. LED brightness = %d", led_brightness)
        info_str = 'M.A.R.S. Rover library available.'
        driveLogger.info(info_str)
        driveCfg.journal_send(info_str)

    def move_rover(dir_deg: float = DIR, speed_per: float = SPEED) -> None:
        """
        Set simple rover steering: direction (left or right) and speed (forward or reverse).
        All motors set to the same speed.

        :param dir_deg: 
            Direction angle value
            ranges from -90.0 to +90.0 (degrees)
            A None value keeps unchnaged the current direction
        :param speed_per: 
            Speed value
            ranges from -100 .0 to 100.0 (percentage of max speed)
        """
        if dir_deg is not None:
            rover.setServo(driveCfg.SERVO_FL, dir_deg)
            rover.setServo(driveCfg.SERVO_FR, dir_deg)
            rover.setServo(driveCfg.SERVO_RL, -1*dir_deg)
            rover.setServo(driveCfg.SERVO_RR, -1*dir_deg)
            driveLogger.debug("Direction=%f", dir_deg)

        if speed_per == 0:
            # Coast to stop
            rover.stop()

            # Set all LED to red
            flash_all_leds(1, 0.1, driveCfg.LED_RED_H)

        elif speed_per > 0:
            # Move forward
            rover.forward(abs(int(speed_per)))

            # Set forward-back left-right LED
            set_rlfb_led(True, dir_deg)

        elif speed_per < 0:
            # Move backward
            rover.reverse(abs(int(speed_per)))

            # Set forward-back left-right LED
            set_rlfb_led(False, dir_deg)

        driveLogger.debug("Speed=%f", speed_per)

    def move_rover_ackerman(dir_deg: float = DIR, speed_per: float = SPEED) -> None:
        """
        Set Ackerman rover steering: direction (left or right) and speed (forward or reverse).
        Left and Right motors can be set to different speeds and angles 
        according to Ackerman steering geometry. 
        See https://www.mathworks.com/help/sm/ug/mars_rover.html
        NOTE: Due to the 4tronix circuit design of the Main Board 
        all three wheels on the same side of the rover are set to the same speed!

        :param dir_deg: 
            Direction angle value (steering angle of the rover)
            ranges from -90.0 to +90.0 (degrees)
            A None value keeps unchanged the current direction
        :param speed_per: 
            Speed value (speed of the rover) 
            ranges from -100.0 to 100.0 (percentage of max speed)
        """

        # Calculate the Ackerman steering parameters
        if dir_deg is not None:
            dir_left, dir_right, speed_left, speed_right = calc_ackerman_steering(
                dir_deg, speed_per)
            prev_dir = dir_deg

            # Apply new steering angles
            rover.setServo(driveCfg.SERVO_FL, dir_left)
            rover.setServo(driveCfg.SERVO_FR, dir_right)
            rover.setServo(driveCfg.SERVO_RL, -1*dir_left)
            rover.setServo(driveCfg.SERVO_RR, -1*dir_right)

        else:
            # Use the last direction value
            dir_deg = prev_dir
            dir_left, dir_right, speed_left, speed_right = calc_ackerman_steering(
                dir_deg, speed_per)

        driveLogger.debug("Direction=%d (left=%d, right=%d)",
                          dir_deg, dir_left, dir_right)

        if speed_per == 0:
            # Coast to stop
            rover.stop()

            speed_left = 0
            speed_right = 0

            # Set all LED to red
            flash_all_leds(1, 0.1, driveCfg.LED_RED_H)

        elif speed_per > 0:
            # Move forward
            rover.turnForward(speed_left, speed_right)

            # Set front-back left-right LEDs
            set_rlfb_led(True, dir_deg)

        elif speed_per < 0:
            # Move backward
            rover.turnReverse(speed_left, speed_right)

            # Set front-back left-right LEDs
            set_rlfb_led(False, dir_deg)

        driveLogger.debug("Speed=%d (left=%d, right=%d)",
                          speed_per, speed_left, speed_right)

    def stop_rover() -> None:
        """
        Coast to stop.
        """

        # Stop rover
        rover.stop()

        # Flash 3 times all LEDs in red
        flash_all_leds(3, 0.5, driveCfg.LED_RED)

        driveLogger.debug('Motors coast to stop!')

    def brake_rover() -> None:
        """
        Brake and stop quickly.
        """
        rover.brake()
        rover.setServo(driveCfg.SERVO_FL, 0)
        rover.setServo(driveCfg.SERVO_FR, 0)
        rover.setServo(driveCfg.SERVO_RL, 0)
        rover.setServo(driveCfg.SERVO_RR, 0)

        # Flash 3 times all LEDs in red
        flash_all_leds(3, 1, driveCfg.LED_RED)

        driveLogger.debug('Motors stop quickly!')

    def cleanup_rover() -> None:
        """
        Cleanup rover library.
        """
        # Rotating LED lights
        seq_all_leds(5, 0.1, driveCfg.LED_RED)

        # Clean exit
        rover.cleanup()

        driveLogger.debug('Rover cleanup!')


# No rover libary - do nothing.
except ImportError:

    def init_rover(led_brightness: int = 0) -> str:
        """
        No rover libary - do nothing.

        :param led_brightness: 
            LEDs default brightness, rnages from 0 to 100
        :return: 
            String with intialisation message
        """
        driveLogger.info('Dummy: Rover initialisation. LED brightness = %d)', led_brightness)
        warn_str = 'M.A.R.S. Rover library is NOT available, using dummy functions!'
        driveLogger.warning(warn_str)
        return warn_str

    def move_rover(dir_deg: float = DIR, speed_per: int = SPEED) -> None:
        """
        No rover libary - print what we would have sent to it if we'd had one.

        :param dir_deg: 
            Direction angle value, ranges from -90.0 to +90.0
            A None value keeps unchnaged the current direction
        :param speed_per: 
            Speed value, ranges from -100 to 100
        """
        driveLogger.info("Dummy: Direction=%d, Speed=%d", dir_deg, speed_per)
        sleep(0.1)

    def move_rover_ackerman(dir_deg: float = DIR, speed_per: int = SPEED) -> None:
        """
        No rover libary - print what we would have sent to it if we'd had one.

        :param dir_deg: 
            Direction angle value, ranges from -90.0 to +90.0
            A None value keeps unchnaged the current direction
        :param speed_per: 
            Speed value, ranges from -100 to 100
        """
        # Calculate the Ackerman steering parameters
        if dir_deg is not None:
            prev_dir = dir_deg
        else:
            # Use the last direction value
            dir_deg = prev_dir
        dir_left, dir_right, speed_left, speed_right = calc_ackerman_steering(dir_deg, speed_per)

        driveLogger.info(
            "Dummy: Direction=%d (left=%d, right=%d)", dir_deg, dir_left, dir_right)

        if speed_per == 0:
            speed_left = 0
            speed_right = 0

        driveLogger.info("Dummy: Speed=%d (left=%d, right=%d)",
                         speed_per, speed_left, speed_right)
        sleep(0.1)

    def stop_rover() -> None:
        """
         No rover libary - do nothing.
        """
        rover.stop()
        driveLogger.info('Dummy: Motors coast to stop!')

    def brake_rover() -> None:
        """
        No rover libary - do nothing.
        """
        driveLogger.info('Dummy: Motors stop quickly!')

    def cleanup_rover() -> None:
        """
        No rover libary - do nothing.
        """
        driveLogger.info('Dummy: rover.cleanup()')

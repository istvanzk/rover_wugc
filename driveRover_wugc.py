# -*- coding: utf-8 -*-
# 4tronix M.A.R.S. Rover Robot remote control using the PiHut Wireless USB Game Controller
# Requires The Pi Zero variant of 4tronix M.A.R.S. Rover Robot
# https://shop.4tronix.co.uk/products/marsrover?variant=31848857043059
#
# Integrates the use of the PiHut Wireless USB Game Controller
# https://thepihut.com/products/raspberry-pi-compatible-wireless-gamepad-controller
# Uses the https://approxeng.github.io/approxeng.input/index.html
# library (https://github.com/ApproxEng/approxeng.input/)
# Inspired by https://approxeng.github.io/approxeng.input/examples/tiny4wd.html
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

"""Main WUGC script"""

# pylint: disable=line-too-long

import os
import sys
from time import sleep
from datetime import datetime, timedelta
import logging
import subprocess
#import tty
#import termios

# Attempt to import approxeng.input library
try:
    # All we need, as we don't care which controller we bind to, is the ControllerResource
    from approxeng.input.selectbinder import ControllerResource
except ImportError:
    logging.error("The approxeng.input library must be installed! Bye!")
    sys.exit()

# Local
from drivelogger import driveLogger
from driveconfig import driveExit, driveCfg
from drivefunc import init_rover, move_rover, move_rover_ackerman, stop_rover, cleanup_rover
from drivefunc import mixer_dir, mixer_speed, rumble_start, rumble_end, seq_all_leds


class RoverStopException(Exception):
    """
    The simplest possible subclass of Exception, we'll raise this if we want to stop the robot
    for any reason. Creating a custom exception like this makes the code more readable later.
    """
    # pass


# Main loop
# Outer try / except catches the RoverStopException to
# bail out of the loop cleanly, shutting the motors down.
ROVER_SPEED = -1
ROVER_DIR = -1
SD_SQUARE = False
SD_CIRCLE = False
SD_CMD = False

RB_TRIANGLE = False
RB_CROSS = False
RB_CMD = False

try:
    # Init the rover
    init_rover(driveCfg.LED_BRIGHT)

    # Notify systemd.daemon
    driveCfg.daemon_notify("READY=1")

    while True:
        # Inner try / except is used to wait for a controller to become available, at which point we
        # bind to it and enter a loop where we read axis values and send commands to the motors.
        try:
            # Bind to any available controller.
            # This will use whatever's connected as long as the library supports it.
            with ControllerResource(dead_zone=0.05, hot_zone=0.05) as pihutwugc:
                INFO_STR = 'Controller found.'
                driveLogger.info(INFO_STR)
                driveCfg.journal_send(INFO_STR)
                #driveLogger.info('Use left stick to set rover speed and right stick to set rover direction. Press Analog button to exit')
                driveLogger.debug(pihutwugc.controls)

                # Update the systemd watchdog
                driveCfg.daemon_notify("WATCHDOG=1")

                # Indicate connection via force-feedback
                rumble_start(pihutwugc)

                # Rotating LED lights
                seq_all_leds(3, 0.2, driveCfg.LED_GREEN)

                # Loop until the pihutwugc disconnects,
                # or we deliberately stop by raising a RoverStopException
                watchdog_tprev = datetime.now()
                while pihutwugc.connected:

                    # Get pihutwugc values from the left and right circular analogue axes
                    #lx_axis, ly_axis, rx_axis, ry_axis = pihutwugc['lx', 'ly', 'rx', 'ry']
                    lx_axis, ly_axis = pihutwugc['l']
                    rx_axis, ry_axis = pihutwugc['r']

                    # Driving modes
                    #pylint: disable=no-member
                    if driveCfg.mainCfg.mode == 'simple':
                        # Get rover speed from mixer function (= rover speed value for all 6 motors)
                        ROVER_SPEED_CURRENT, _ = mixer_speed(
                            yaw=0,
                            throttle=ly_axis)

                        # Get rover direction from mixer function (= angle value for all 4 motors)
                        ROVER_DIR_CURRENT = mixer_dir(
                            l_r=rx_axis,
                            f_b=ry_axis,
                            max_dir=30)

                        # Set rover rover direction and rover speed
                        if ROVER_SPEED != ROVER_SPEED_CURRENT or ROVER_DIR != ROVER_DIR_CURRENT:
                            move_rover(
                                dir_deg=ROVER_DIR_CURRENT,
                                speed_per=ROVER_SPEED_CURRENT)
                            ROVER_DIR = ROVER_DIR_CURRENT
                            ROVER_SPEED = ROVER_SPEED_CURRENT

                    elif driveCfg.mainCfg.mode == 'ackermann':
                        # Get rover speed from mixer function (= speed of the rover)
                        ROVER_SPEED_CURRENT, _ = mixer_speed(
                            yaw=0,
                            throttle=ly_axis)

                        # Get rover direction from mixer function (= steering angle of the rover)
                        ROVER_DIR_CURRENT = mixer_dir(
                            l_r=rx_axis,
                            f_b=ry_axis)

                        # Set rover rover direction and rover speed
                        if ROVER_SPEED != ROVER_SPEED_CURRENT or ROVER_DIR != ROVER_DIR_CURRENT:
                            move_rover_ackerman(
                                dir_deg=ROVER_DIR_CURRENT,
                                speed_per=ROVER_SPEED_CURRENT)
                            ROVER_DIR = ROVER_DIR_CURRENT
                            ROVER_SPEED = ROVER_SPEED_CURRENT
                    #pylint: enable=no-member

                    # Get a ButtonPresses object containing everything that was pressed
                    # since the last time around this loop.
                    # The PiHut controller Turbo button is not currently mapped
                    # to any button in the API!
                    pihutwugc.check_presses()

                    # Print out any buttons that were pressed, if we had any
                    if pihutwugc.has_presses:
                        driveLogger.debug(pihutwugc.presses)

                    # If square was pressed, ...
                    held_square = pihutwugc.square
                    if held_square is not None:

                        if held_square >= driveCfg.SHUTDOWN_HELD:
                            SD_SQUARE = True

                    # If circle was pressed, ...
                    held_circle = pihutwugc.circle
                    if held_circle is not None:

                        if held_circle >= driveCfg.SHUTDOWN_HELD:
                            SD_CIRCLE = True

                    # Initiate RPi shutdown
                    if SD_SQUARE and SD_CIRCLE:
                        SD_CMD = True
                        INFO_STR = 'Initiate RPi shutdown!'
                        driveLogger.info(INFO_STR)
                        raise RoverStopException()

                    SD_SQUARE = False
                    SD_CIRCLE = False

                    # If triangle was pressed, ...
                    held_triangle = pihutwugc.triangle
                    if held_triangle is not None:

                        if held_triangle >= driveCfg.REBOOT_HELD:
                            RB_TRIANGLE = True

                    # If cross was pressed, ...
                    held_cross = pihutwugc.cross
                    if held_cross is not None:

                        if held_cross >= driveCfg.REBOOT_HELD:
                            RB_CROSS = True

                    # Initiate RPi reboot
                    if RB_TRIANGLE and RB_CROSS:
                        RB_CMD = True
                        INFO_STR = 'Initiate RPi reboot!'
                        driveLogger.info(INFO_STR)
                        raise RoverStopException()
                    RB_TRIANGLE = False
                    RB_CROSS = False

                    # If start was pressed, ...
                    # if pihutwugc.start:

                    # The PiHut controller Analog button is mapped to the home button in the API
                    held_home = pihutwugc.home
                    if held_home is not None and held_home >= driveCfg.HOME_HELD:

                        INFO_STR = 'Program stopped by the User'
                        driveLogger.info(INFO_STR)
                        driveCfg.journal_send(INFO_STR)
                        raise RoverStopException()

                    # This exception will be rised for SIGINT, SIGTERM and SIGABRT
                    if driveExit.kill_now:
                        raise RoverStopException()

                    # Update the systemd watchdog when needed
                    watchdog_tcrt = datetime.now()
                    if watchdog_tcrt - watchdog_tprev > timedelta(seconds=int(1.0*driveCfg.WATCHDOG_USEC/2000000.0)):
                        driveCfg.daemon_notify("WATCHDOG=1")
                        watchdog_tprev = watchdog_tcrt

        except IOError:
            # We get an IOError when using the ControllerResource if we don't have a controller yet,
            # so in this case we just wait a second and try again after printing a message.
            INFO_STR = 'No controller found yet. Keep trying!'
            driveLogger.info(INFO_STR)
            driveCfg.journal_send(INFO_STR)
            sleep(1)
            # pass

        # Update the systemd watchdog
        sleep(1.0*driveCfg.WATCHDOG_USEC/3000000.0)
        driveCfg.daemon_notify("WATCHDOG=1")

except RoverStopException:
    # This exception will be raised when
    # - for the home button pressed
    # - for SIGINT, SIGTERM and SIGABRT events
    # - for reboot/shutdown commmands
    stop_rover()
    rumble_end(pihutwugc)

    INFO_STR = 'Stop rover and clean exit.'
    driveLogger.info(INFO_STR)
    driveCfg.journal_send(INFO_STR)

    # Close the rover library
    cleanup_rover()

    # Notify systemd.daemon
    # This will not lead to a re-start!
    driveCfg.daemon_notify("STOPPING=1")

# Handle shutdown or reboot
finally:
    if SD_CMD:
        driveLogger.info('Shutdown initiated with ./sd.sh')
        #os.system('(sleep 3 && sudo shutdown now)&')
        _grab_cmd = subprocess.Popen(os.path.join(os.path.ROVER_DIRname(
            __file__), "sd.sh"), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        _cmdoutput, _cmderrors = _grab_cmd.communicate()
        driveLogger.debug(
            "Shutdown cmd: output: %s, error: %s", _cmdoutput, _cmderrors.decode())

    elif RB_CMD:
        driveLogger.info('Reboot initiated ./rb.sh')
        #os.system('(sleep 3 && sudo reboot)&')
        _grab_cmd = subprocess.Popen(os.path.join(os.path.ROVER_DIRname(
            __file__), "rb.sh"), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        _cmdoutput, _cmderrors = _grab_cmd.communicate()
        driveLogger.debug(
            "Reboot cmd: output: %s, error: %s", _cmdoutput, _cmderrors.decode())

    # Shutdown logging
    logging.shutdown()

    sleep(1)

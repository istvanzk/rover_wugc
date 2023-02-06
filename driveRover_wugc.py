# -*- coding: utf-8 -*-
# 4tronix M.A.R.S. Rover Robot remote control using the PiHut Wireless USB Game Controller
# Requires The Pi Zero variant of 4tronix M.A.R.S. Rover Robot
# https://shop.4tronix.co.uk/products/marsrover?variant=31848857043059
#
# Integrates the use of the PiHut Wireless USB Game Controller
# https://thepihut.com/products/raspberry-pi-compatible-wireless-gamepad-controller
# Uses the https://approxeng.github.io/approxeng.input/index.html library (https://github.com/ApproxEng/approxeng.input/)
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

import os
#import sys
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
    os._exit()

# Local
from drivelogger import driveLogger
from driveconfig import driveExit, driveCfg
from drivefunc import initRover, moveRover, stopRover, brakeRover, cleanupRover, mixerDir, mixerSpeed, rumbleStart, rumbleEnd, flashAllLED, seqAllLED

class RoverStopException(Exception):
    """
    The simplest possible subclass of Exception, we'll raise this if we want to stop the robot
    for any reason. Creating a custom exception like this makes the code more readable later.
    """
    pass

### Main loop
# Outer try / except catches the RoverStopException to
# bail out of the loop cleanly, shutting the motors down.
speed = -1
dir   = -1
shutdown_square = False
shutdown_circle = False
shutdown_cmd    = False

reboot_triangle = False
reboot_cross    = False
reboot_cmd      = False

try:
    # Init the rover
    initRover(driveCfg.LED_BRIGHT)

    # Notify systemd.daemon
    driveCfg.daemon_notify("READY=1")

    while True:
        # Inner try / except is used to wait for a controller to become available, at which point we
        # bind to it and enter a loop where we read axis values and send commands to the motors.
        try:
            # Bind to any available controller. 
            # This will use whatever's connected as long as the library supports it.
            with ControllerResource(dead_zone=0.1, hot_zone=0.2) as pihutwugc:
                info_str = 'Controller found.'
                driveLogger.info(info_str)
                driveCfg.journal_send(info_str)
                #driveLogger.info('Use left stick to set speed and right stick to set direction. Press Analog button to exit')
                driveLogger.debug(pihutwugc.controls)

                # Update the systemd watchdog
                driveCfg.daemon_notify("WATCHDOG=1")

                # Indicate connection via force-feedback
                rumbleStart(pihutwugc)

                # Rotating LED lights
                seqAllLED(3, 0.2, driveCfg.LED_GREEN) 

                # Loop until the pihutwugc disconnects, 
                # or we deliberately stop by raising a RoverStopException
                watchdog_tprev = datetime.now()
                while pihutwugc.connected:

                    # Get pihutwugc values from the left and right circular analogue axes
                    #lx_axis, ly_axis, rx_axis, ry_axis = pihutwugc['lx', 'ly', 'rx', 'ry']
                    lx_axis, ly_axis = pihutwugc['l']
                    rx_axis, ry_axis = pihutwugc['r']

                    # Driving modes
                    if driveCfg.mainCfg.mode == 'simple':
                        # Get speed from mixer function (for one speed value for all motors)
                        speed_current, _ = mixerSpeed(yaw=0, throttle=ly_axis)

                        # Get direction from mixer function
                        dir_current = mixerDir(lr=rx_axis, fb=ry_axis)

                        # Set rover direction and speed
                        if speed != speed_current or dir != dir_current:
                            moveRover(dir=dir_current, speed=speed_current)
                            dir = dir_current
                            speed = speed_current


                    # Get a ButtonPresses object containing everything that was pressed since the last
                    # time around this loop.
                    # The PiHut controller Turbo button is not currently mapped to any button in the API!
                    pihutwugc.check_presses()

                    # Print out any buttons that were pressed, if we had any
                    if pihutwugc.has_presses:
                        driveLogger.debug(pihutwugc.presses)


                    # If square was pressed, ...
                    held_square = pihutwugc.square
                    if held_square is not None:

                        if held_square >= driveCfg.SHUTDOWN_HELD:
                            shutdown_square = True

                    # If circle was pressed, ...
                    held_circle = pihutwugc.circle
                    if held_circle is not None:

                        if held_circle >= driveCfg.SHUTDOWN_HELD:
                            shutdown_circle = True


                    # Initiate RPi shutdown
                    if shutdown_square and shutdown_circle:
                        shutdown_cmd = True
                        info_str = 'Initiate RPi shutdown!'
                        driveLogger.info(info_str)
                        raise RoverStopException()
                    else:
                        shutdown_square = False
                        shutdown_circle = False
    

                    # If triangle was pressed, ...
                    held_triangle = pihutwugc.triangle
                    if held_triangle is not None:

                        if held_triangle >= driveCfg.REBOOT_HELD:
                            reboot_triangle = True

                    # If cross was pressed, ...
                    held_cross = pihutwugc.cross
                    if held_cross is not None:

                        if held_cross >= driveCfg.REBOOT_HELD:
                            reboot_cross = True

                    # Initiate RPi reboot
                    if reboot_triangle and reboot_cross:
                        reboot_cmd = True
                        info_str = 'Initiate RPi reboot!'
                        driveLogger.info(info_str)
                        raise RoverStopException()
                    else:
                        reboot_triangle = False
                        reboot_cross    = False
        
                    # If start was pressed, ...
                    #if pihutwugc.start:


                    # The PiHut controller Analog button is mapped to the home button in the API
                    held_home = pihutwugc.home
                    if held_home is not None and held_home >= driveCfg.HOME_HELD:

                        info_str = 'Program stopped by the User'
                        driveLogger.info(info_str)
                        driveCfg.journal_send(info_str)
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
            info_str = 'No controller found yet. Keep trying!'
            driveLogger.info(info_str)
            driveCfg.journal_send(info_str)
            sleep(1)
            pass

        # Update the systemd watchdog
        sleep(1.0*driveCfg.WATCHDOG_USEC/3000000.0)
        driveCfg.daemon_notify("WATCHDOG=1")

except RoverStopException:
    # This exception will be raised when 
    # - for the home button pressed
    # - for SIGINT, SIGTERM and SIGABRT events
    # - for reboot/shutdown commmands
    stopRover()
    rumbleEnd(pihutwugc)

    info_str = 'Stop rover and clean exit.'
    driveLogger.info(info_str)
    driveCfg.journal_send(info_str)

    # Close the rover library
    cleanupRover()

    # Notify systemd.daemon
    # This will not lead to a re-start!
    driveCfg.daemon_notify("STOPPING=1")

### Handle shutdown or reboot
finally:
    if shutdown_cmd:
        driveLogger.info('Shutdown initiated with ./sd.sh')
        #os.system('(sleep 3 && sudo shutdown now)&')
        _grab_cmd = subprocess.Popen(os.path.join(os.path.dirname(__file__), "sd.sh"), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        
        _cmdoutput, _cmderrors = _grab_cmd.communicate()
        driveLogger.debug(f"Shutdown cmd: output: {_cmdoutput}, error: {_cmderrors.decode()}")

    elif reboot_cmd:
        driveLogger.info('Reboot initiated ./rb.sh')
        #os.system('(sleep 3 && sudo reboot)&')
        _grab_cmd = subprocess.Popen(os.path.join(os.path.dirname(__file__), "rb.sh"), stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        _cmdoutput, _cmderrors = _grab_cmd.communicate()
        driveLogger.debug(f"Reboot cmd: output: {_cmdoutput}, error: {_cmderrors.decode()}")

    # Shutdown logging
    logging.shutdown()

    sleep(1)

### Done.
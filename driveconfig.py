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

"""Implements the driveRover_wugc configuration """

# pylint: disable=invalid-name
# pylint: disable=line-too-long

import os
import sys
import socket
import subprocess
import signal
from dataclasses import dataclass, field
from drivelogger import driveLogger
try:
    import yaml
except ImportError as e:
    driveLogger.error("YAML module could not be loaded!")
    sys.exit()

try:
    from systemd import daemon
    from systemd import journal
    SYSTEMD_MOD = True
except ImportError as e:
    driveLogger.warning("The Python systemd module was not found. Continuing without SystemD features.")
    SYSTEMD_MOD = False
    #pass

class Struct(object):
    """Custom object for converting dict to object"""

    def __init__(self, **dict_):
        self.__dict__.update(dict_)
    def __repr__(self):
        _s=", ".join('%s: %s' % (k, repr(v)) for (k, v) in self.__dict__.items())
        return f"<{_s:s}>"

@dataclass
class DriveConfig:
    """The class setting and storing all the config parameters"""
    ## Custom configuration START

    # Configuration file
    YAMLCFG_FILE: str = field(default="driveconfig.yaml")

    # Internet connection
    INTERNETUSE: bool = field(default=True)

    # SystemD use
    SYSTEMDUSE: bool = field(default=True)

    # Force-feedback use
    # NOT enabled in the Raspbian kernel (Jan 2023)!
    FFDEVICEUSE: bool = field(default=False)

    ## Custom configuration END




    ## OS
    HOST_NAME: str = field(default="none")
    WATCHDOG_USEC: float = field(default = 15.0)
    FF_DEVICE: str = field(default="")

    ## Rover physical parameters
    # The ratio between the left-right wheel distance (chasis width) and
    # the front-back wheel distance (chassis length)
    DoL: float = field(default=80.0/77.0)
    # The wheel radius (mm)
    WhR: float = field(default=45.0/2.0)

    ## Rover servo motor IDs
    # See https://4tronix.co.uk/blog/?p=2409
    SERVO_FL: int = field(default = 9)
    SERVO_RL: int = field(default = 11)
    SERVO_FR: int = field(default = 15)
    SERVO_RR: int = field(default = 13)
    SERVO_MP: int = field(default = 0)
    SERVO_MT: int = field(default = 1)

    ## Rover LEDs
    LED_BRIGHT: int = field(default = 0)
    LED_NUM: int = field(default = 0)
    LED_RED: int = field(default = 0)
    LED_ORANGE: int = field(default = 0)
    LED_GREEN: int = field(default = 0)
    LED_BLUE: int = field(default = 0)
    LED_BLACK: int = field(default = 0)
    LED_WHITE: int = field(default = 0)
    LED_RED_H: int = field(default = 0)
    LED_ORANGE_H: int = field(default = 0)
    LED_GREEN_H: int = field(default = 0)
    LED_BLUE_H: int = field(default = 0)
    LED_WHITE_H: int = field(default = 0)

    ## The number of seconds the Analog/Home button
    # has to be pressed to activate the driveRover_wugc stop
    HOME_HELD: int = field(default = 3)

    ## Shutdown and reboot button combination held times
    SHUTDOWN_HELD: int = field(default = 3)
    REBOOT_HELD: int = field(default = 3)

    ## Button held times for custom actions
    SQUARE_HELD: int = field(default = 1)
    CIRCLE_HELD: int = field(default = 1)
    TRIANG_HELD: int = field(default = 1)
    CROSS_HELD: int = field(default = 1)

    ## Parameters read from YAML config file
    mainCfg: dict = field(default = None)
    auxCfg: dict = field(default = None)
    ledCfg: dict = field(default = None)
    mastCfg: dict = field(default = None)
    camCfg: dict = field(default = None)

    ## Post init function
    def __post_init__(self):

        # Python version
        PY39 = (sys.version_info[0] == 3) and (sys.version_info[1] >= 9)
        if not PY39:
            driveLogger.error("This program requires minimum Python 3.9!")
            sys.exit()

        # Hostname
        self.HOST_NAME = subprocess.check_output(["hostname", ""], shell=True).strip().decode('utf-8')

        # When the DNS server google-public-dns-a.google.com is reachable on port 53/tcp,
        # then the internet connection is up and running.
        if self.INTERNETUSE:
            try:
                socket.setdefaulttimeout(10)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
                driveLogger.info("Internet connection available.")

            except TimeoutError:
                driveLogger.info("Internet connection NOT available. Continuing in off-line mode.")
                self.INTERNETUSE = False
                #pass
        else:
            self.INTERNETUSE = False
            driveLogger.info("Internet connection not used.")


        # Use systemd features when available
        if SYSTEMD_MOD:
            self.SYSTEMDUSE = daemon.booted()
            if self.SYSTEMDUSE:
                try:
                    self.WATCHDOG_USEC = int(os.environ['WATCHDOG_USEC'])

                except KeyError:
                    driveLogger.warning("Environment variable WATCHDOG_USEC is not set (yet?).")
                    #pass

                driveLogger.info("SystemD features used: READY=1, STATUS=, WATCHDOG=1 (WATCHDOG_USEC=%d), STOPPING=1.", self.WATCHDOG_USEC)

            else:
                driveLogger.warning("The system is not running under SystemD. Continuing without SystemD features.")

        else:
            driveLogger.info("SystemD features not used.")


        # Read the configuration parameters
        if self.YAMLCFG_FILE is not None:
            try:
                with open(self.YAMLCFG_FILE, 'r', encoding='utf-8') as stream:
                    _maincfg, _auxcfg, _ledcfg, _mastcfg, _camcfg = yaml.load_all(stream, Loader=yaml.SafeLoader)

                driveLogger.info("YAML configuration file read.")

            except yaml.YAMLError as _e:
                driveLogger.error("Error in YAML configuration file: %s", _e)
                sys.exit()

            ## Convert config info to objects
            self.mainCfg = Struct(**_maincfg)
            driveLogger.debug("driveCfg: %s", self.mainCfg)

            self.auxCfg = Struct(**_auxcfg)
            driveLogger.debug("auxCfg: %s", self.auxCfg)

            # Settings based on the read config params
            #pylint: disable=no-member
            if self.auxCfg.led:
                self.ledCfg = Struct(**_ledcfg)
                driveLogger.debug("ledCfg: %s", self.ledCfg)

                # Rover LEDs colors
                #pylint: disable=import-outside-toplevel
                from rover import numPixels, fromRGB
                self.LED_BRIGHT = self.ledCfg.led_bright
                self.LED_NUM    = numPixels
                self.LED_RED    = fromRGB(255,0,0)
                self.LED_ORANGE = fromRGB(255,255,0)
                self.LED_GREEN  = fromRGB(0,255,0)
                self.LED_BLUE   = fromRGB(0,0,255)
                self.LED_BLACK  = fromRGB(0,0,0)
                self.LED_WHITE  = fromRGB(255,255,255)
                self.LED_RED_H    = fromRGB(100,0,0)
                self.LED_ORANGE_H = fromRGB(100,100,0)
                self.LED_GREEN_H  = fromRGB(0,100,0)
                self.LED_BLUE_H   = fromRGB(0,0,100)
                self.LED_WHITE_H  = fromRGB(100,100,100)
                #pylint: enable=import-outside-toplevel

            if self.auxCfg.mast:
                self.mastCfg = Struct(**_mastcfg)
                driveLogger.debug("mastCfg: %s", self.mastCfg)

                self.SERVO_MP = self.mastCfg.servo_pan
                if self.mastCfg.mast_type == 'pantilt':
                    self.SERVO_MT = self.mastCfg.servo_tilt

            if self.auxCfg.cam:
                self.camCfg = Struct(**_camcfg)
                driveLogger.debug("camCfg: %s", self.camCfg)

            #pylint: enable=no-member

        # Force-feedback config (if any)
        if not self.FFDEVICEUSE:
            self.FF_DEVICE = None
            driveLogger.warning("Force-feedback events are not enabled!")


    ## SystemD functions
    def journal_send(self, msg_str: str) -> None:
        """ Send a message to the journald """
        if self.SYSTEMDUSE:
            journal.send(msg_str)

    def daemon_notify(self, msg_str: str) -> None:
        """ Send notification message to the systemd daemon """
        if self.SYSTEMDUSE:
            daemon.notify(msg_str)


driveCfg = DriveConfig()
driveLogger.info(driveCfg)

class GracefulKiller:
    """Gracefull exit class"""
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        signal.signal(signal.SIGABRT, self.exit_gracefully)

        driveLogger.info("Set gracefull exit handling for SIGINT, SIGTERM and SIGABRT.")

    def exit_gracefully(self, signum, frame):
        """Set the exit flag"""
        self.kill_now = True

driveExit = GracefulKiller()

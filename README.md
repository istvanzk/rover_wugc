# 4tronix M.A.R.S. Rover Robot remote control using the PiHut Wireless USB Game Controller

![Exp](https://img.shields.io/badge/Fork-experimental-orange.svg)
[![Lic](https://img.shields.io/badge/License-Apache2.0-green)](http://www.apache.org/licenses/LICENSE-2.0)
![Py](https://img.shields.io/badge/python-3.9+-green)
![Ver](https://img.shields.io/badge/version-1.2-blue)

## Sources, references, dependencies

* The Pi Zero variant of [4tronix M.A.R.S. Rover Robot](https://shop.4tronix.co.uk/products/marsrover?variant=31848857043059)
* The original code from 4tronix M.A.R.S. Rover, installed as explained in [Programming M.A.R.S. Rover on
Raspberry Pi Zero (inc v2)](https://4tronix.co.uk/blog/?p=2409)
* The [PiHut Wireless USB Game Controller](https://thepihut.com/products/raspberry-pi-compatible-wireless-gamepad-controller) [WUGC]
* Dependencies: [`rover.py` and `pca9685.py`](https://4tronix.co.uk/blog/?p=2409), [`RPi.GPIO`](https://pypi.org/project/RPi.GPIO/), [`aproxeng.input`](https://approxeng.github.io/approxeng.input/index.html), [`rpi_ws281x`](https://pypi.org/project/rpi-ws281x/), [`python3-systemd`](https://github.com/systemd/python-systemd), `dataclasses`, `PyYAML`, `python3-smbus`
  - The [rpi_ws281x](https://pypi.org/project/rpi-ws281x/) module is the official Python binding for the [userspace Raspberry Pi library for controlling WS281X LEDs](https://github.com/jgarff/rpi_ws281x), and uses _/dev/mem_ for DMA/PWM/PCM and _/dev/gpiomem_  for GPIO access (see [ws2811.c](https://github.com/jgarff/rpi_ws281x/blob/master/ws2811.c)).  **Therefore, the LED control on the Rover works only with root access!**

## Version history
### V1.0, February 2023

* Joysticks:
  * Use left stick to set speed (forward or reverse) and right stick to set direction (left or right). 
* Buttons:
  * Analog for 3 sec to exit program (and stop the service unit). 
  * Circle+Square for 3 sec to initiate system shutdown with `./sd.sh`.
  * Triangle+Cross for 3 sec to initiate system reboot with `./rb.sh`.
* LEDs (**must be run with root access**):
  * Initialisationn light sequence.
  * White color in the front; red color in back; etc.
  * Program termination light sequence.
* Simple driving mode: all (6) DC motors are driven with the same speed. Direction is set only by the servo motors.
* Logging to (rotating) log file `./driverover.log` and console.
* Use [systemd service unit](https://www.freedesktop.org/software/systemd/man/systemd.service.html#) to start, monitor (watchdog) and re-start the `driverRover_wugc.py` on missed watchdog; has to be installed as system-wide unit (root access) when LEDs are used!
* Use YAML configuration file `./driveconfig.yaml` for most common custom parameters; other parameters are configured in `driveconfig.py`.

### V1.1, March 2023
* Implement [Ackermann steering](https://en.wikipedia.org/wiki/Ackermann_steering_geometry) driving mode (with hwd limitations). Can be set in `driverconfg.yaml` with `mode: 'ackerman'`.
### V1.2, March 2023
* Scale direction angle in the function `mixer_dir()` in `drivefunc.py`.
* Code clean-up. Fix most of the pylint errors and warnings (except in the orginal code `rover.py`, etc.)


## TODOs:
  * Power management for low battery detection - needs external battery voltage monitoring circuit
  * Push button activated power-on/off with clean shutdown - currently a clean shutdown or reboot can be initiated from the WUGC only (see above)
  




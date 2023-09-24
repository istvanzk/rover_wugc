# 4tronix M.A.R.S. Rover Robot remote control using the PiHut Wireless USB Game Controller

![Exp](https://img.shields.io/badge/Fork-experimental-orange.svg)
[![Lic](https://img.shields.io/badge/License-Apache2.0-green)](http://www.apache.org/licenses/LICENSE-2.0)

The `scripts` folder contains the [systemd service unit](https://www.freedesktop.org/software/systemd/man/systemd.service.html#) files and bash scripts required to support the system-wide services/daemons described below. 
The `gpio_test.sh` is a bash script which can be used to test the GPIO monitoring loops.
The `install.sh` is a bash script which can be used to install the service units (copy, enable and check status).

### Installation (as root, with sudo)
* The service unit files `*.service` must be installed in `/lib/systemd/system/`. 
* The `gpio-poweroff.sh` must be installed in `/usr/lib/systemd/system-shutdown/`.
* The other bash scripts must remain in this `scripts` folder.

## Run driveRover_wugc.py as service

The `driverover.service` unit file implements the execution of the `../driveRover_wugc.py` as _Type=notify_ service.

### Dependecies
* Main Python code in `/home/pi/rover_wugc/`
* `sd.sh` shutdown/poweroff bash script initiated from `driveRover_wugc.py` (via the remote controller)
* `rb.sh` reboot bash script initiated from `driveRover_wugc.py` (via the remote controller)
* `gpio-poweroff.sh` bash script which triggers the hardware poweroff GPIO pin after system poweroff

## Push button activated power-on/off with clean shutdown/poweroff service

Implemented in `cleansd.service` unit file for the execution of the `cleansd.sh` as _Type=exec_ service.

### Dependecies
* `cleansd.sh` bash script for daemon to monitor the push button GPIO pin and trigger the system poweroff
* `cleansdfunc.sh` common bash functions for the `cleansd.sh` and `battsd.sh` daemons
* `gpio-poweroff.sh` bash script which triggers the hardware poweroff GPIO pin after system poweroff

## Low battery triggered clean shutdown/poweroff service

Implemented in `battsd.service` unit file for the execution of the `battsd.sh` as _Type=exec_ service.

### Dependecies
* `battsd.sh` bash script for daemon to monitor the battery-low GPIO pin and trigger the system poweroff
* `cleansdfunc.sh` common bash functions for the `cleansd.sh` and `battsd.sh` daemons
* `gpio-poweroff.sh` bash script which triggers the hardware poweroff GPIO pin after system poweroff

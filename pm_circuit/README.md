# 4tronix M.A.R.S. Rover Robot remote control using the PiHut Wireless USB Game Controller

![Exp](https://img.shields.io/badge/Use-Experimental-orange.svg)
[![Lic](https://img.shields.io/badge/License-Apache2.0-green)](http://www.apache.org/licenses/LICENSE-2.0)
![Ver](https://img.shields.io/badge/version-1.3-blue)

## Description

This is a prototype Power Management Add-on Circuit (PMAC) for the M.A.R.S. Rover Robot main board. 
The orginal main board **does not require any modifications**. 

* The core of the PMAC is based on the [Raspberry Pi ON/OFF Power Controller](http://www.mosaic-industries.com/embedded-systems/microcontroller-projects/raspberry-pi/on-off-power-controller) circuit.
* The PMAC is enabled by having the orginal power switch of the M.A.R.S. Rover Robot in OFF position. 
* When the power is off, one push on the SW0 (<1sec) will power up the board and the Raspbery Pi. When the power is on, a longer push on SW0 (~4 sec) initiates the shutdown/poweroff of the Raspeberry Pi and the power off of the main board after that. See [`scripts`](scripts) for details.
  * GPIO 17 is used to monitor the SW0 trigger.
  * GPIO 27 is used to monitor the battery level trigger.
  * GPIO 22 is used to initiate the PMAC hardware poweroff.
  * The GPIO 17 and 22 are used innstead of a single GPIO to avoid the possibility of forced shutdown via SW0.)
* The [MAX8212](https://www.analog.com/en/products/max8212.html) is used to detect when the voltage level on the battery pack drops below 4.6V.
* The logical level converter [BOB-12009](https://www.sparkfun.com/products/12009) is used to interface to the Rasperberry Pi Zero GPIOs.
* All components except the Logical level converter are soldered on a prototyping board, which is attached with two screws to the back end of the M.A.R.S. Rover Robot main board.

## Connections

* The PMAC is connected to the main board through the J1-J2 and J3-J4 connectors.
* J2 has its wires soldered to the corresponding pads on the main board.
* J3 is available on the M.A.R.S. main board, and can be any of the SVx connectors used for the step-motors.
* J6 has its wires soldered to the HVx pads on the Logical level converter board ([BOB-12009](https://www.sparkfun.com/products/12009))
* J11 is soldered to the Lx pads onn the Logical level converter board ([BOB-12009](https://www.sparkfun.com/products/12009))
* J12 is mounted on a [ModMyPi's Raspberry Pi Zero Prototyping pHAT](https://core-electronics.com.au/modmypi-zero-prototyping-phat-zero.html) 

## BOM

|# |Reference|Qty|Value|
|:---|:---|:---|:---|
|1|C1|1|1uF|
|2|C2, C4|2|0.1uF|
|3|C3|1|10uF or 22uF|||
|4|D1, D2|2|1N4148|
|5|R1, R6, R11, R12, R13, R14, R15, R16|8|10K|
|6|R2, R4|2|100K|
|7|R3|1|330K|
|8|R5, R7|2|100R|
|9|R8|1|168K|
|10|R9|1|470K|
|11|R10|1|32K|
|12|J1|1|01x02_Pin|
|13|J2|1|01x02_Socket|
|14|J3|1|01x03_Pin|
|15|J4|1|01x03_Socket|
|16|J5|1|01x04_Pin|
|17|J6|1|01x04_Socket|
|18|J9|1|01x02_Pin|
|19|J10|1|01x02_Socket|
|20|J11|1|01x06_Pin|
|21|J12|1|01x06_Socket|
|22|SW0|1|Mom. button|
|23|Q1A, Q1B|1|[IRF7319IPBF](https://www.infineon.com/dgdl/irf7319pbf.pdf?fileId=5546d462533600a4015355f5c82f1b41)|
|24|U3|1|[MAX8212](https://www.analog.com/en/products/max8212.html)|
|25|LC|1|[BOB-12009](https://www.sparkfun.com/products/12009)|
|26|pHAT for J12|1|[ModMyPi's Raspberry Pi Zero Prototyping pHAT](https://core-electronics.com.au/modmypi-zero-prototyping-phat-zero.html) |
|




#!/bin/bash

# Common functions for the cleansd.sh and battsd.sh daemons
# Based on https://github.com/pimoroni/clean-shutdown/ and https://github.com/petrockblog/PowerBlock
# - Log events are written into syslog at /var/log/syslog.

# Common path for all GPIO access
BASE_GPIO_PATH=/sys/class/gpio

# Logging
DO_LOGGING=1

# ------------------- FUNCTION DEFINITIONS ---------------

checkForRoot() {
  # check if run as root
  if [ "$EUID" -ne 0 ]
    then echo "ERROR: These fucntions need to be run as root!"
    exit
  fi
}

# Exports a pin if not already exported
# Parameter $1: pin number
exportPin() {
  if [ ! -e $BASE_GPIO_PATH/gpio$1 ]; then
    echo "$1" > $BASE_GPIO_PATH/export
  fi
}

unexportPin() {
  if [ ! -e $BASE_GPIO_PATH/gpio$1 ]; then
    echo "$1" > $BASE_GPIO_PATH/unexport
  fi
}

# Set a pin as an output
# Parameter $1: pin number to be set as output pin
setDirectionOutput() {
  echo "out" > $BASE_GPIO_PATH/gpio$1/direction
}

# Set value of a pin
# Parameter $1: pin number
# Parameter $2: output value. Can be 0 or 1
setPinValue() {
  echo $2 > $BASE_GPIO_PATH/gpio$1/value
}

# Set a pin as an output
# Parameter $1: pin number to be set as output pin
setDirectionInput() {
  echo "in" > $BASE_GPIO_PATH/gpio$1/direction
}

# Returns the current pin value
# Parameter $1: pin number to be read from
getPinValue() {
  echo $(cat $BASE_GPIO_PATH/gpio$1/value)
}

# If the logger is enabled then log events into syslog at /var/log/syslog
write_log() 
{
  if [ "$DO_LOGGING" -eq "1" ]; then
    while read text
    do 
      logger -t driverover-gpio $text
    done
  fi
}
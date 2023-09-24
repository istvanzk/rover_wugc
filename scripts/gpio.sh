#!/bin/bash

# Common path for all GPIO access
BASE_GPIO_PATH=/sys/class/gpio

# Assign names to states
STATE_ON="0"
STATE_OFF="1"

# Input pins (BCM)
SHUTDOWN_PIN=17
BATSTATUS_PIN=27


checkForRoot() {
  # check if run as root
  if [ "$EUID" -ne 0 ]
    then echo "ERROR: needs to be run as root."
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

# Set a pin as an output
# Parameter $1: pin number to be set as output pin
setDirectionInput() {
  echo "in" > $BASE_GPIO_PATH/gpio$1/direction
}

# Set value of a pin
# Parameter $1: pin number
# Parameter $2: output value. Can be 0 or 1
setPinValue() {
  echo $2 > $BASE_GPIO_PATH/gpio$1/value
}

# Returns the current pin value
# Parameter $1: pin number to be read from
getPinValue() {
  echo $(cat $BASE_GPIO_PATH/gpio$1/value)
}

doShutdown() {
  #exec $SHUTDOWNSCRIPT &
  echo "Executing shutdown script..."

  exportPin $SHUTDOWN_PIN
  setDirectionOutput $SHUTDOWN_PIN
  echo "Set SHD pin to 0"
  setPinValue $SHUTDOWN_PIN 0
  sleep 5  
  
  stopRunning
}


stopRunning() {
  echo "Exiting script."
  unexportPin $BATSTATUS_PIN
  unexportPin $SHUTDOWN_PIN  
  exit
}


# --- START ---

checkForRoot

exportPin $BATSTATUS_PIN
exportPin $SHUTDOWN_PIN

setDirectionInput $BATSTATUS_PIN
setDirectionInput $SHUTDOWN_PIN

# Ctrl-C handler for clean shutdown
trap stopRunning SIGINT
trap stopRunning SIGQUIT
trap stopRunning SIGABRT
trap stopRunning SIGTERM

isShutdownRunning=0
while [ 1 ]
do
  sleep 1
  batValue=$(getPinValue $BATSTATUS_PIN)
  echo "BAT: $batValue"
  shdValue=$(getPinValue $SHUTDOWN_PIN)
  echo "SHD: $shdValue"
  if [ $shdValue -eq $STATE_ON ]; then
    if [ $isShutdownRunning -eq 0 ]; then
      echo "Shutdown signal observed"
      doShutdown
      isShutdownRunning=1
    fi
  fi
done


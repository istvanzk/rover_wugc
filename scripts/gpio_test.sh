#!/bin/bash

# Script to test GPIO monitoring daemons
# Based on https://github.com/pimoroni/clean-shutdown/ and https://github.com/petrockblog/PowerBlock

# Common path for all GPIO access
BASE_GPIO_PATH=/sys/class/gpio

# Input pins (BCM)
TRIGGER_PIN=17
STATE_ON=0
TRIGG_HOLD_TIME=3

BATTERY_PIN=27
STATE_OFF=1
BATT_BUFFER_LNG=30
BATT_TRIGG_COUNT=20

POLLING_RATE=1

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
  echo "Executing fake shutdown script."
  unexportPin $BATTERY_PIN
  unexportPin $TRIGGER_PIN  
  exit 0
}


stopRunning() {
  echo "Exiting test script."
  unexportPin $BATTERY_PIN
  unexportPin $TRIGGER_PIN  
  exit 0
}

fifoBuff(){
    if [ "${#batt[@]}" -eq "$BUFF_LNG" ]; then
        batt=("${batt[@]:1}")
        batt[$BATT_BUFF_LNG-1]=$1
    else
        batt[${#batt[@]}]=$1
    fi
}

batt_trigger(){
    crt_count=0
    for v in "${batt[@]}"; do
        if [ "$v" -eq "$STATE_OFF" ]; then
            crt_count=$((crt_count+1))
        fi
    done
    if [ "$crt_count" -ge "$BATT_TRIGG_COUNT" ]; then
        return 0
    fi
    return 1
}

shutdown_trigger() {
    trigValue=$(getPinValue $TRIGGER_PIN)
    if [ $trigValue -eq "$STATE_ON" ]]; then
        echo "BCM $TRIGGER_PIN asserted $STATE_ON" | write_log
        start=$SECONDS

        while [ $trigValue -eq "$STATE_ON" ]; do
            sleep 0.1
            low_time=$[ $SECONDS - $start ]
            if [ "$low_time" -ge "$TRIGG_HOLD_TIME" ]; then
                break
            fi
            trigValue=$(getPinValue $TRIGGER_PIN)
        done

        if [ "$low_time" -ge "$TRIGG_HOLD_TIME" ]; then
            echo "BCM $TRIGGER_PIN held low for $low_time seconds" | write_log
            return 0
        fi
    fi
    return 1
}

# --- START TEST SEQUENCE ---
echo "Start test script."

checkForRoot

exportPin $BATTERY_PIN
exportPin $TRIGGER_PIN

setDirectionInput $BATTERY_PIN
setDirectionInput $TRIGGER_PIN

# Ctrl-C handler for clean shutdown
trap stopRunning SIGINT
trap stopRunning SIGQUIT
trap stopRunning SIGABRT
trap stopRunning SIGTERM

batt[0]=0
crt_count=1
while true; do
  shdValue=$(getPinValue $TRIGGER_PIN)
  echo "TRIG: $shdValue"
  if shutdown_trigger; then
    echo "Shutdown button detected."
    doShutdown
  fi

  batValue=$(getPinValue $BATTERY_PIN)
  echo "BATT: $batValue"
  fifoBuff $batValue
  if batt_trigger; then
    echo "Battery-low trigger detected."
    doShutdown
  fi
  echo "Batt: ${batt[*]}"
  echo "L:${#batt[@]}, T:$crt_count"
 
  sleep $POLLING_RATE

done

exit 0
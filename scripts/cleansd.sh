#!/bin/bash

# Button sensing triggered shutdown/poweroff daemon
# Based on https://github.com/pimoroni/clean-shutdown/ and https://github.com/petrockblog/PowerBlock
# - Uses functions from cleansdfunc.sh
# - Does not use any external configuration file
# - Uses poweroff instead of shutdown
# - Log events are written into syslog at /var/log/syslog
# - The hardware poweroff is iniated with gpio-poweroff.sh
# - Script is run as a systemd service with cleansd.service

# Daemon control
DAEMON_ACTIVE=1
BASE_SCRIPTS=/home/pi/rover_wugc/scripts
SHUTDOWNSCRIPT=$BASE_SCRIPTS/sd.sh
SHUTDOWNFUNC=$BASE_SCRIPTS/cleansdfunc.sh

# Trigger/button sensing pin (BCM) and shutdown parameters 
TRIGGER_PIN=17
STATE_ON=0
TRIGG_HOLD_TIME=3
TRIGG_POLLING_RATE=1

# ------------------- FUNCTION DEFINITIONS ---------------

# Source the functions
if [ -f "$SHUTDOWNFUNC" ]; then
    source $SHUTDOWNFUNC
else
    echo "$SHUTDOWNFUNC does not exist. Exiting cleansd daemon."
    exit 1
fi

shutdown_trigger() {
    trigValue=$(getPinValue $TRIGGER_PIN)
    if [ "$trigValue" -eq "$STATE_ON" ]; then
        echo "BCM $TRIGGER_PIN asserted $STATE_ON" | write_log
        start=$SECONDS

        while [ "$trigValue" -eq "$STATE_ON" ]; do
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

doShutdown() {
  echo "Executing power down... " | write_log
  unexportPin $TRIGGER_PIN
  #exec $SHUTDOWNSCRIPT &
  poweroff
}

stopRunning() {
  unexportPin $TRIGGER_PIN
  echo "Exiting cleansd daemon" | write_log
  exit 0
}

# ---------------- BEGIN OF MAIN PART ------------------

checkForRoot

# Check if the shutdown script is enabled
if grep -q "^[[:space:]]*disable_cleanshutd=1" /boot/config.txt; then
    echo "cleansd is disabled in /boot/config.txt" | write_log
    exit 1
elif [ "$DAEMON_ACTIVE" == 0 ]; then
    echo "cleansd is disabled in script" | write_log
    exit 1
fi

# BCM pin setup
exportPin $TRIGGER_PIN
setDirectionInput $TRIGGER_PIN
echo "Monitoring BCM $TRIGGER_PIN" | write_log

# Ctrl-C handlers
trap stopRunning SIGINT
trap stopRunning SIGQUIT
trap stopRunning SIGABRT
trap stopRunning SIGTERM

# Daemon loop
daemon="on"
while true; do
    while [ "$daemon" = "on" ]; do
        if shutdown_trigger; then
            msg="User button initiated system power down"
            echo $msg | write_log
            wall $msg
            daemon="off"
            doShutdown
            break
        fi
        sleep $TRIGG_POLLING_RATE
    done

    while [ "$daemon" = "off" ]; do
        if [ ! -f /var/run/nologin ]; then
            exportPin $TRIGGER_PIN
            setDirectionInput $TRIGGER_PIN
            daemon="on"
            break
        fi
        sleep $TRIGG_POLLING_RATE
    done
done

# Never get here?
exit 0
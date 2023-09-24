#!/bin/bash

# Battery sensing triggered shutdown/poweroff daemon
# Based on https://github.com/pimoroni/clean-shutdown/ and https://github.com/petrockblog/PowerBlock
# - Uses functions from cleansdfunc.sh
# - Does not use any external configuration file
# - Uses poweroff instead of shutdown
# - Log events are written into syslog at /var/log/syslog
# - The hardware poweroff is iniated with gpio-poweroff.sh
# - Script is run as a systemd service with battsd.service

# Daemon control
DAEMON_ACTIVE=1
BASE_SCRIPTS=/home/pi/rover_wugc/scripts
SHUTDOWNSCRIPT=$BASE_SCRIPTS/sd.sh
SHUTDOWNFUNC=$BASE_SCRIPTS/cleansdfunc.sh

# Battery sensing pin (BCM) and shutdown parameters 
BATTERY_PIN=27
STATE_ON=1
BATT_POLLING_RATE=1
BATT_BUFFER_LNG=30
BATT_TRIGG_COUNT=20

# ------------------- FUNCTION DEFINITIONS ---------------

# Source the functions
if [ -f "$SHUTDOWNFUNC" ]; then
    source $SHUTDOWNFUNC
else
    echo "$SHUTDOWNFUNC does not exist. Exiting battsd daemon."
    exit 1
fi

fifoBuff(){
    if [ "${#batt[@]}" -eq "$BATT_BUFFER_LNG" ]; then
        batt=("${batt[@]:1}")
        batt[$BATT_BUFFER_LNG-1]=$1
    else
        batt[${#batt[@]}]=$1
    fi
}

batt_trigger(){
    crt_count=0
    for v in "${batt[@]}"; do
        if [ "$v" -eq "$STATE_ON" ]; then
            crt_count=$((crt_count+1))
        fi
    done
    if [ "$crt_count" -ge "$BATT_TRIGG_COUNT" ]; then
        return 0
    fi
    return 1
}

doShutdown() {
  echo "Executing power down... " | write_log
  unexportPin $BATTERY_PIN
  #exec $SHUTDOWNSCRIPT &
  poweroff
}

stopRunning() {
  unexportPin $BATTERY_PIN
  echo "Exiting battsd daemon" | write_log
  exit 0
}

# ---------------- BEGIN OF MAIN PART ------------------

checkForRoot

# Check if the shutdown script is enabled
if grep -q "^[[:space:]]*disable_battshutd=1" /boot/config.txt; then
    echo "battsd is disabled in /boot/config.txt" | write_log
    exit 1
elif [ "$DAEMON_ACTIVE" == 0 ]; then
    echo "battsd is disabled in script" | write_log
    exit 1
fi

# BCM pin setup
exportPin $BATTERY_PIN
setDirectionInput $BATTERY_PIN
echo "Monitoring BCM $BATTERY_PIN" | write_log

# Ctrl-C handlers
trap stopRunning SIGINT
trap stopRunning SIGQUIT
trap stopRunning SIGABRT
trap stopRunning SIGTERM

# Daemon loop
daemon="on"
batt[0]=0
crt_count=1
while true; do
    while [ "$daemon" = "on" ]; do
        fifoBuff $(getPinValue $BATTERY_PIN)
        if batt_trigger; then
            msg="Battery low initiated system power down"
            echo $msg | write_log
            wall $msg
            daemon="off"
            doShutdown
            break
        fi
        sleep $BATT_POLLING_RATE
    done

    while [ "$daemon" = "off" ]; do
        if [ ! -f /var/run/nologin ]; then
            exportPin $BATTERY_PIN
            setDirectionInput $BATTERY_PIN
            daemon="on"
            break
        fi
        sleep $BATT_POLLING_RATE
    done
done

# Never get here?
exit 0
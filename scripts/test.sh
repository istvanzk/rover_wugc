#!/bin/bash

# Daemon control
DAEMON_ACTIVE=1
BASE_SCRIPTS=/Users/izk/Documents/Soft/MARSRob/rover_wugc/scripts
SHUTDOWNSCRIPT=$BASE_SCRIPTS/sd.sh
SHUTDOWNFUNC=$BASE_SCRIPTS/cleansdfunc.sh

BUFF_LNG=30
TRIGG_COUNT=17

# Source the functions
if [ -f "$SHUTDOWNFUNC" ]; then
    source $SHUTDOWNFUNC
else
    echo "$SHUTDOWNFUNC does not exist. Exiting cleansd daemon."
    exit 1
fi

#echo "$DO_LOGGING"
#echo "$BASE_GPIO_PATH"

stopRunning() {
    echo "Final"
    echo ${batt[*]}
    echo ${#batt[@]}
    echo $crt_count
    exit 0
}

countBuff(){
    crt_count=0
    for v in "${batt[@]}"; do
        if [ "$v" -eq "1" ]; then
            crt_count=$((crt_count+1))
        fi
    done
    if [ "$crt_count" -ge "$TRIGG_COUNT" ]; then
        return 0
    fi
    return 1
}

fifoBuff(){
    if [ "${#batt[@]}" -eq "$BUFF_LNG" ]; then
        batt=("${batt[@]:1}")
        batt[$BUFF_LNG-1]=$1
    else
        batt[${#batt[@]}]=$1
    fi
}

# Ctrl-C handlers
trap stopRunning SIGINT
trap stopRunning SIGQUIT
trap stopRunning SIGABRT
trap stopRunning SIGTERM

batt[0]=0
crt_count=1
while true; do
    sleep 1
    if [ "$RANDOM" -ge 16383 ]; then
        fifoBuff 1
    else
        fifoBuff 0
    fi
    echo ${batt[*]}
    echo ${#batt[@]}
    echo $crt_count
    if countBuff; then
        echo "Trigger reached"
        stopRunning
    fi
done

exit 0
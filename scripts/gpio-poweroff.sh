#!/bin/bash

# Based on https://github.com/pimoroni/clean-shutdown/
# sudo cp gpio-poweroff.sh /usr/lib/systemd/system-shutdown/gpio-poweroff.sh
# $1 will be either "halt", "poweroff", "reboot" or "kexec"

# https://www.freedesktop.org/software/systemd/man/systemd-halt.service.html
# Shortly before executing the actual system power-off/halt/reboot/kexec systemd-shutdown 
# will run all executables in /usr/lib/systemd/system-shutdown/ and pass one arguments to them: 
# either "poweroff", "halt", "reboot", or "kexec", depending on the chosen action. 
# All executables in this directory are executed in parallel, and execution of the action is 
# not continued before all executables finished. Note that these executables are run after all 
# services have been shut down, and after most mounts have been detached (the root file system 
# as well as /run/ and various API file systems are still around though). 
# This means any programs dropped into this directory must be prepared to run in such a limited 
# execution environment and not rely on external services or hierarchies such as /var/ to be 
# around (or writable).

SHUTDOWN_PIN=22
SHUTDOWN_SLEEP=12

case "$1" in
  poweroff | halt)
        if [ "$SHUTDOWN_PIN" = "" ]; then
            /bin/echo "Skipping GPIO power-off" && exit 0
        else
            /bin/echo "Using power off pin $SHUTDOWN_PIN"
        fi
        /bin/echo "$SHUTDOWN_PIN" > /sys/class/gpio/export
        /bin/echo "out" > /sys/class/gpio/gpio$SHUTDOWN_PIN/direction
        /bin/echo 0 > /sys/class/gpio/gpio$SHUTDOWN_PIN/value
        /bin/sleep $SHUTDOWN_SLEEP
        ;;
esac
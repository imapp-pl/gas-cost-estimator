#!/bin/bash

if [ `cat /sys/devices/system/clocksource/clocksource0/current_clocksource` != 'tsc' ]; then
  echo "clocksource should be tsc, found:"
  cat /sys/devices/system/clocksource/clocksource0/current_clocksource
  echo "see docker_timer.md somewhere in the docses"
fi

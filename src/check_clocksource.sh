#!/bin/sh
set -xe

if    [ `cat /sys/devices/system/clocksource/clocksource0/current_clocksource` != 'tsc' ] \
   && [ "$SKIP_CLOCKSOURCE_CHECK" != true ]; then
  echo "clocksource should be tsc, found:"
  cat /sys/devices/system/clocksource/clocksource0/current_clocksource
  echo "see docker_timer.md somewhere in the docses"
  exit 1
fi

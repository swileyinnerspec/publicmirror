#!/bin/bash
BAT=/sys/class/power_supply/BAT1/capacity
APPOINTMENTS=diary

function d() {
 cd && cd stuff
 test -e $BAT && cat  $BAT && expr "$(cat /sys/class/power_supply/BAT1/capacity)" "<" "5" &&  echo "low battery" | festival --tts
 vmstat -S m
 ./tt stats
 ./tt kanban
 ./showappointments
 tail ~/note
}
d

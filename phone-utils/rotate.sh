#!/bin/ash

# 1 0 0
# 0 1 0
# 0 0 1
# 1 0 0 0 1 0 0 0 1

# 0-1 1
# 1 0 0
# 0 0 1
# 0-1 1 1 0 0 0 0 1

if [ $1 = "left" ]; then
xrandr -o left
xinput set-prop 8 --type=float "Coordinate Transformation Matrix" 0 -1 1 1 0 0 0 0 1
./.fehbg
else
xrandr -o normal
xinput set-prop 8 --type=float "Coordinate Transformation Matrix" 1 0 0 0 1 0 0 0 1
./.fehbg
fi


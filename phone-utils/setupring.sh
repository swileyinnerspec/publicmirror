#!/usr/bin/env sh

echo 'AT+QURCCFG="urcport","all"' |tee -| sudo atinout - /dev/EG25.AT -

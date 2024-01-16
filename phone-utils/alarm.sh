#!/bin/bash
#This might not behave correctly durring leap seconds, timezone crossings, long sleeps, etc.
alarmtime=$(date --date="$1" +%s)
dist=$(expr $alarmtime - $(date +%s))
if [ $dist -gt 0 ]
then
echo $dist
else
alarmtime=$(expr $alarmtime + 86400 )
fi
vtring() {
echo -e "\a"
sleep 1
echo -e "\a"
sleep 1
echo -e "\a"
sleep 1
echo -e "\a"
sleep 1
echo -e "\a"
}
sleeptime() {
dist=$(expr $alarmtime - $(date +%s))
echo $dist
}
echo "will sleep for aproximately $(sleeptime) seconds"
while [ $(sleeptime) -gt 0 ]
do
echo $(sleeptime) remains
sleep 5
done
echo "alarm expires"
#sudo openrc default #TODO: determine if we're on a phone with a sleeping runlevel
sleep 3
#sudo ~/dial.sh hup
while true
do
#DISPLAY=:0 fbcli -t 1 -E alarm-clock-elapsed || vtring
ffplay ~/alarm.webm
sleep 5
done

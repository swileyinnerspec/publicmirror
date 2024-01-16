#!/bin/ash
function dialnumber {
sudo -u swiley setupcallaudio -m -h -e -s
sudo -u swiley setupcallaudio -m -h -e -s
sudo -u swiley setupcallaudio -m -h -e -s -2
sudo -u swiley setupcallaudio -m -h -e -s -2
echo "dialing $1"
echo "ATD$1;" |tee -| atinout - /dev/EG25.AT -
sleep 5
sudo -u swiley setupcallaudio -m -h -e -s
sudo -u swiley setupcallaudio -m -h -e -s
sudo -u swiley setupcallaudio -m -h -e -s -2
sudo -u swiley setupcallaudio -m -h -e -s -2

}
if [ $1 = "hup" ]; then
sudo -u swiley setupcallaudio -m -h -e -s -2
sudo -u swiley setupcallaudio -m -h -e -s
echo "ATH" | tee - | atinout - /dev/EG25.AT -
exit 0
elif [ $1 = "answer" ]; then
killall calls
sudo -u swiley setupcallaudio -m -h -e -s
sudo -u swiley setupcallaudio -m -h -e -s
sudo -u swiley setupcallaudio -m -h -e -s -2
sudo -u swiley setupcallaudio -m -h -e -s -2
echo "ATA" | tee - | atinout - /dev/EG25.AT -
sleep 3
sudo -u swiley setupcallaudio -m -h -e -s
sudo -u swiley setupcallaudio -m -h -e -s
sudo -u swiley setupcallaudio -m -h -e -s -2
sudo -u swiley setupcallaudio -m -h -e -s -2
exit 0
fi

if [ $1 = ""]; then
echo "enter a phone number to call"
dialnumber $(read)
exit 0
fi
dialnumber $1

#!/bin/bash
CONVOPATH="$HOME/.aiconvo"
MODELPATH=$(cat /etc/gptjpath)
DEFAULTCONVO=/etc/gptjdefaultcontext
echo "conversation from $CONVOPATH, model from $MODELPATH"
if [ ! -f $CONVOPATH ]; then
	cp $DEFAULTCONVO $CONVOPATH
fi
echo $* >>$CONVOPATH
echo -n "Bot: " | tee -a $CONVOPATH
gpt-j -s 1 -b 100 -m $MODELPATH -Q -p CONVOPATH --temp .5 -r "Human:" -p "$(cat $CONVOPATH)" | tee -a $CONVOPATH 

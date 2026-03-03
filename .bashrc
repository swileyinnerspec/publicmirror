# /etc/skel/.bashrc
#
# This file is sourced by all *interactive* bash shells on startup,
# including some apparently interactive shells such as scp and rcp
# that can't tolerate any output.  So make sure this doesn't display
# anything or bad things will happen !


# Test for an interactive shell.  There is no need to set anything
# past this point for scp and rcp, and it's important to refrain from
# outputting anything in those cases.
if [[ $- != *i* ]] ; then
	# Shell is non-interactive.  Be done now!
	return
fi


# Put your fun stuff here.
export PATH=$PATH:$HOME/.local/bin
GUIX_PROFILE="$HOME/.guix-profile"
#.  "$GUIX_PROFILE/etc/profile"
#.  $GUIX_PROFILE
trap 'echo -ne "\033]2;$(history 1 | sed "s/^[ ]*[0-9]*[ ]*//g")\007"' DEBUG
export HISTFILESIZE=
export HISTSIZE=
export HISTTIMEFORMAT="[%F %T $USER@$HOSTNAME] "
export HISTFILE=~/stuff/bash_history
PS1="[\u@$HOSTNAME]:\W \t\n\$ "
PROMPT_COMMAND="history -a; $PROMPT_COMMAND"
export PATH=$PATH:/usr/local/go/bin/
export PATH=$PATH:$HOME/go/bin/
export PATH=$PATH:$HOME/stuff/bin/
export PATH=$PATH:$HOME/stuff/
export TTDB=$HOME/stuff/todo.ini
export OPENAI_API_BASE=http://localhost:8013/v1
export OPENAI_API_KEY=sk-local


export EDITOR=nvim
speak_readline_text() {
    # Festival requires the text to be echoed into its `--tts` mode
    echo "$READLINE_LINE" | festival --tts
}
bind -x '"\C-xs": speak_readline_text'

bind '"\C-x\C-v": "$(xsel -b)\e\C-e"'
source .ssh-agent.sh >/dev/null

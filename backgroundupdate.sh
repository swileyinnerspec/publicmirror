#!/usr/bin/env printf "This file should not be marked executable"
function eschtml () {
	sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g; s/'"'"'/\&#39;/g'
}
function update {
	git reset --hard
	git branch -r | grep -v '\->' | sed "s,\x1B\[[0-9;]*[a-zA-Z],,g" | while read remote; do git branch --track "${remote#origin/}" "$remote"; done
	git fetch --all
	git pull
	echo "<title>Public data for mail.swiley.net</title><h1>Readme.html</h1>">./.head.html
	cat .head.html readme.html >.index.html
	rm .head.html
	rm branches.html
	echo "<pre>" >>./.index.html
	if [ -e tt.c ]
	then
		echo "</pre><hr><h1>Scrum Board</h1><pre>" >>./.index.html
		cc tt.c && ./a.out kanban >>./.index.html; rm a.out
	fi
	rm index.html
	echo "</pre><hr><h1>Reposotory data</h1><pre>" >>./.index.html
	tree | awk '/^ *(│|├|─|└)+.*/{
    pretext=$0
    gsub(/│/,"")
    gsub(/(│|├|─|└)+/," ")
    findent = length($0)
    gsub(/^( | )+/,"")
    gsub(/^[[:space:]]+/,"")
    indent=int((findent-length($0))/4+1)
    path[indent] = $0

    for (i = indent + 1; i <= prev_indent; i++) {
        delete path[i]
    }

    prev_indent = indent

    full_path = "."
    for (i = 1; i <= indent; i++) {
        full_path = full_path "/" path[i]
    }

    print "<a href=\"" full_path "\">" pretext "</a>"
    next
}
{print $0}
' >>./.index.html
	du -sh >>./.index.html
	git branch >>./.index.html
	echo "</pre><p> Go to <a href='branches.html'>Mergable branches</a>" >>./.index.html
	echo "</pre><h2>Commits</h2><pre>" >>./.index.html
	git log --oneline | eschtml >>./.index.html
	if [ -e ci.sh ]
	then
		d="$(date +%s)"
		(./ci.sh >./ci.$d.log >>./.index.html) & #even after the move it should be fine.
	fi
	echo -n "</pre><hr>Updated and copyright " >>./.index.html
	date >>./.index.html
	mv .index.html index.html
	cd .git && git update-server-info && cd ..
}
function branches () {
	rm branches.html
	echo "<head><title>Branches</title></head>" >./branches.html
	echo "<h1>Branches</h1>" >>./branches.html
	for branch in $(git branch --no-merged)
	do
		echo "<h2 name=\"$branch\"> diff for $branch </h2><pre>" >>./branches.html
		if which ansi2html
		then
		git diff -R --color "$branch" | eschtml |ansi2html -w -n >>./branches.html
		else
		git diff -R "$branch"  | eschtml >>./branches.html
		fi
		echo "</pre>" >>./branches.html
	done
}

update
branches

inotifywait -r "$(git config --get remote.origin.url)";
sleep 5
exec bash "${BASH_SOURCE[0]}"


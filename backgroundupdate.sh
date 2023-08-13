#!/usr/bin/env printf "This file should not be marked executable"
function update {
	git reset --hard
	git pull
	echo "<title>Public data for mail.swiley.net</title><h1>Readme.html</h1>">./.head.html
	cat .head.html readme.html >.index.html
	rm .head.html
	echo "<pre>" >>./.index.html
	if [ -e tt.c ]
	then
		echo "</pre><hr><h1>Scrum Board</h1><pre>" >>./.index.html
		cc tt.c && ./a.out kanban >>./.index.html; rm a.out
	fi
	rm index.html
	echo "</pre><hr><h1>Reposotory data</h1><pre>" >>./.index.html
	tree | awk '{
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

    print "<a href=\"" full_path "\">" pretext "<//a>"
echo '</pre>'
}'>>./.index.html
	du -sh >>./.index.html
	git branch >>./.index.html
	echo "</pre><h2>Commits</h2><pre>" >>./.index.html
	git log --oneline >>./.index.html
	echo -n "</pre><hr>Updated and copyright " >>./.index.html
	date >>./.index.html
	mv .index.html index.html
	cd .git && git update-server-info && cd ..
}

update
inotifywait -r "$(git config --get remote.origin.url)";
sleep 5
exec bash "${BASH_SOURCE[0]}"


function update {
	git reset --hard
	git pull
	echo "<title>Docs repo</title><h1>Readme.html</h1>">./.index.html
	cp readme.html .index.html
	echo "<pre>" >>./.index.html
	if [ -e tt.c ]
	then
		echo "</pre><hr><h1>Scrum Board</h1><pre>" >>./.index.html
		cc tt.c && ./a.out kanban >>./.index.html; rm a.out
	fi
	rm index.html
	echo "</pre><hr><h1>Reposotory data</h1><pre>" >>./.index.html
	tree >>./.index.html
	git branch >>./.index.html
	echo "</pre><hr><h2>Commits</h2><pre>" >>./.index.html
	git log --oneline >>./.index.html
	echo -n "</pre><hr>Updated and copyright" >>./.index.html
	date >>./.index.html
	mv .index.html index.html
}
update
while 1 do
	inotifywait "$(git config --get remote.origin.url)";
	update
done

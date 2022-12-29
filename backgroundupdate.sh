function update {
	git reset --hard
	git pull
	echo "<title>git repo</title><h1>Readme.html</h1>">./index.html
	cp readme.html index.html
	echo "<hr><h1>Reposotory data</h1><pre>" >>./index.html
	tree >>./index.html
	git branch >>./index.html
	echo "</pre><hr><h2>Commits</h2><pre>" >>./index.html
	git log --oneline >>./index.html
}
update
while inotifywait -m "$(git config --get remote.origin.url)"; do
	update
done

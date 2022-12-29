function update {
	echo "update!"
	git reset --hard
	git pull
	cp readme index.html
	echo "<pre>" >>./index.html
	tree >>./index.html
	git branch >>./index.html
	git log --oneline >>./index.html
}
update
while inotifywait -m "$(git config --get remote.origin.url)"; do
	update
done

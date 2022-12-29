while inotifywait -m "$(git config --get remote.origin.url)"; do
	echo "update!"
	git reset --hard
	git pull
	cp readme index.html
	echo "<pre>" >>./index.html
	tree >>./index.html
	git log --oneline >>./index.html
done

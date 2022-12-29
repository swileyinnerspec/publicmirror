while inotifywait -m "$(git config --get remote.origin.url)"; do
	echo "update!"
	git pull
	cp readme.html index.html
	echo "<pre>" >>./index.html
	tree >>./index.html
	git log --oneline >>./index.html
done

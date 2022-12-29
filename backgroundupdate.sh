while inotifywait -m "$(git config --get remote.origin.url)"; do
	echo "update!"
	git pull
done

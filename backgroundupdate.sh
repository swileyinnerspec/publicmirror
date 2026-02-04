#!/usr/bin/env printf "This file should not be marked executable"
function eschtml () {
	sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g; s/'"'"'/\&#39;/g'
}
function update {
	git reset --hard
	git branch -r | grep -v '\->' | sed "s,\x1B\[[0-9;]*[a-zA-Z],,g" | while read remote; do git branch --track "${remote#origin/}" "$remote" 2>/dev/null; done
	git fetch --all
	git pull
	
	# Clean up CI logs older than 1 year
	find . -maxdepth 1 -name 'ci.*.log' -type f -mtime +365 -delete
	
	echo "<meta charset='UTF-8'><title>Repository</title><h1>Readme.html</h1>">./.head.html
	cat .head.html readme.html >.index.html 2>/dev/null || echo "<p>No readme.html found</p>" >.index.html
	rm -f .head.html
	rm -f branches.html
	echo "<pre>" >>./.index.html
	if [ -e tt.c ]
	then
		echo "</pre><hr><h1>Scrum Board</h1><pre>" >>./.index.html
		cc tt.c && ./a.out kanban >>./.index.html; rm -f a.out
	fi
	rm -f index.html
	echo "</pre><hr><h1>Repository data</h1><pre>" >>./.index.html
	tree | awk '
BEGIN {
	path[0] = "."
	depth = 0
}
/^ *(│|├|─|└)+.*/ {
	# Save original line for display
	original = $0
	
	# Count the tree structure depth by counting the number of tree chars
	# Each level adds tree characters
	line = $0
	
	# Remove tree drawing characters to get the filename
	gsub(/^[[:space:]]*/, "", line)  # Remove leading spaces
	gsub(/^[│├└─ ]+/, "", line)      # Remove tree characters
	gsub(/^[[:space:]]*/, "", line)  # Remove spaces after tree chars
	
	filename = line
	
	# Calculate depth by counting sets of tree characters
	# Each indent level is typically "│   " (4 chars) or "├── " or "└── "
	temp = $0
	# Count leading spaces and tree characters
	match(temp, /^[[:space:]│├└─]*/)
	prefix_len = RLENGTH
	
	# Estimate depth - each level is roughly 4 characters of indentation
	new_depth = int(prefix_len / 4)
	
	# Build full path
	path[new_depth] = filename
	
	# Clear deeper paths
	for (i = new_depth + 1; i in path; i++) {
		delete path[i]
	}
	
	# Construct full path
	full_path = "."
	for (i = 1; i <= new_depth; i++) {
		if (i in path) {
			full_path = full_path "/" path[i]
		}
	}
	
	# Output with link
	print "<a href=\"" full_path "\">" original "</a>"
	next
}
{
	# Non-tree lines, print as-is
	print $0
}
' >>./.index.html
	du -sh >>./.index.html
	git branch >>./.index.html
	echo "</p><p> Go to <a href='branches.html'>Mergable branches</a>" >>./.index.html
	echo "</pre><h2>Commits</h2><pre>" >>./.index.html
	git log --oneline | eschtml >>./.index.html
	if [ -e ci.sh ]
	then
		d="$(date +%s)"
		(./ci.sh >./ci.$d.log 2>&1) & #even after the move it should be fine.
	fi
	echo -n "</pre><hr>Updated and copyright " >>./.index.html
	date >>./.index.html
	mv .index.html index.html
	cd .git && git update-server-info && cd ..
}
function branches () {
	rm -f branches.html
	echo "<head><title>Branches</title></head>" >./branches.html
	echo "<h1>Branches</h1>" >>./branches.html
	for branch in $(git branch --no-merged)
	do
		echo "<h2 name=\"$branch\"> diff for $branch </h2><pre>" >>./branches.html
		if which ansi2html >/dev/null 2>&1
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
# Get the filesystem path of the origin repository
ORIGIN_PATH="$(git config --get remote.origin.url | sed 's|^file://||')"
# Monitor the entire origin repository for changes
inotifywait -m -r -e modify,create,delete,move "$ORIGIN_PATH" --format '%w%f' | while read change
do
	sleep 5
	exec bash "${BASH_SOURCE[0]}"
done
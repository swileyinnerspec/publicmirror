:set mouse= 			"Let Xterm manage the selection buffer
:set spell				"This works with syntax on in NeoVim
:set number				"Line numbers
:set rnu				"relative line numbers
set list				"Make Whitespace visible
:set visualbell			"Vim should not touch the bell
:syntax on				"Rainbows aren't just for the gays
:set so=999				"Cursor should be in the middle of the screen
:set incsearch			"see next
:set hlsearch			"Higlhight text as you type search/subst expr
:set laststatus=0		"Type :messages if you want to see it
:set inccommand=nosplit "Can't remember
set title				"Set title string so cwm can search for the window
:set cursorline			"Make cursor more visible
:hi NonText cterm=none  ctermbg=black ctermfg=black
match NonText '^\s\+'
set listchars=tab:⇒⠠,trail:␣,extends:⇒,precedes:< "Schow Whitespace
set noexpandtab			"Tabs encode the idea of an indentation level
set shiftwidth=4		"Rather than its presentation
set tabstop=4
filetype plugin indent off "Can't remember
set colorcolumn=78		"Highlight margin so we don't run it over.

"Maps and user commands
:set makeprg=/home/swiley/stuff/smartmake\ %	"Sort of like plumb
command Wmake :w | :make
"Meta M write file and run smartmake
map <M-m> <esc>:Wmake<cr>
"Meta E Run command from cursor to end of line (so you can put macros in comments)
map <M-e> <esc>:exec getline('.')[col('.'):]<cr>
"show changes
map <M-d> <esc>:w !diff % -<cr>
"Run AI
map <M-a> <esc>:w !~/llama.cpp/bin/main -m ~/Downloads/stable-code-3b.Q4_K_M.gguf --log-disable --simple-io -p getline('.')[col('.'):]<cr> 


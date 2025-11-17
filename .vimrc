" ============================
" Basic Settings
" ============================
:set mouse=			  "Let Xterm manage the selection buffer
:set termguicolors
:set spell			   "Spell checking works with syntax on in NeoVim
:set number			  "Line numbers
:set rnu				 "Relative line numbers
:set list				"Make whitespace visible
:set visualbell		  "Vim should not touch the bell
:syntax on			   "Enable syntax highlighting
:set so=999			  "Cursor should be in the middle of the screen
:set incsearch		   "Incremental search
:set hlsearch			"Highlight search matches
:set laststatus=0		"Hide status line
:set inccommand=nosplit  "Incremental command preview
:set title			   "Set window title
:set cursorline		  "Highlight current line
:set cursorcolumn		"Highlight current column
:hi NonText cterm=none ctermbg=black ctermfg=black
match NonText '^\s\+'
set listchars=tab:⇒⠠,trail:␣,extends:⇒,precedes:< "Show whitespace
set noexpandtab		  "Tabs instead of spaces
set shiftwidth=4
set tabstop=4
filetype plugin indent off
set colorcolumn=78	   "Highlight margin

call llama#init()		"Enable local llama completion

" ============================
" Compile / Run mappings
" ============================
:set makeprg=/home/swiley/stuff/smartmake\ % "Custom make program
command Wmake :w | :make

map <M-m> <esc>:Wmake<cr>
map <M-e> <esc>:exec getline('.')[col('.'):]<cr>
map <M-d> <esc>:w !diff % -<cr>

" ============================
" TTS Helper Functions
" ============================
let g:lastmessage = ""

function! SpeakChar() abort
	let l:char = getline('.')[col('.') - 1]

	" Map whitespace
	if l:char ==# "\t"
		let l:char = "tab"
	elseif l:char ==# " "
		let l:char = "space"
	endif

	" Map common punctuation
	let l:punct = {
				\ ':': 'colon',
				\ ';': 'semicolon',
				\ ',': 'comma',
				\ '.': 'dot',
				\ '!': 'bang',
				\ '@': 'com. at.',
				\ '#': 'hash',
				\ '$': 'dollar',
				\ '%': 'percent',
				\ '^': 'circum flex',
				\ '&': 'andpersand',
				\ '~': 'tildeh',
				\ '|': 'pipe',
				\ '(': 'left parenthesis',
				\ ')': 'right parenthesis',
				\ '{': 'left brace',
				\ '}': 'right brace',
				\ '[': 'left bracket',
				\ ']': 'right bracket',
				\ '+': 'plus',
				\ '-': 'minus',
				\ '*': 'asterisk',
				\ '/': 'slash',
				\ '\': 'backslash',
				\ '=': 'equals',
				\ '"': 'double quote',
				\ "'": 'single quote',
				\ "a": 'Ay',
				\ "A": 'Ay'
				\ }

	if has_key(l:punct, l:char)
		let l:char = l:punct[l:char]
	endif

	call system('echo "' . l:char . '" | festival --tts &')
endfunction

function! SpeakWord() abort
	let g:suppress_mode_tts = 1
	let l:word = expand('<cword>')
	if l:word ==# ''
		let l:word = 'blank'
	endif
	call system('echo "' . l:word . '" | festival --tts &')
	let g:suppress_mode_tts = 0
endfunction

function! SpeakPos() abort
	call system('echo "Line ' . line('.') . ' of ' . line('$') . '" | festival --tts &')
endfunction

function! ReadLastMessage() abort
	let current_message = execute("1messages")
	let current_message = substitute(current_message, "\n", " ", "g")
	call system('echo "' . escape(current_message,'#') . '" | festival --tts &')
	echo current_message
endfunction

function! CheckMessages(timer_id) abort
	let current_message = execute("1messages")
	if g:lastmessage != current_message
		let g:lastmessage = current_message
		call ReadLastMessage()
	endif
endfunction

function! SpeakSearchCount() abort
	if v:event.cmdtype == '/' || v:event.cmdtype == '?'
		let matches = searchcount({'maxcount':0})
		let msg = printf("match %d of %d matches", matches.current, matches.total)
		call system('echo "' . msg . '" | festival --tts &')
	endif
endfunction

" ============================
" Speak search match count
" ============================
function! SpeakSearchCountForKey() abort
	let matches = searchcount({'maxcount':0})
	let msg = printf("match %d of %d matches", matches.current, matches.total)
	call system('echo "' . msg . '" | festival --tts &')
endfunction


" ============================
" Speak Buffer Name
" ============================
function! SpeakBufferName() abort
	let l:bufname = bufname('%')
	if l:bufname ==# ''
		let l:bufname = '[No Name]'
	endif
	call system('echo "' . l:bufname . '" | festival --tts &')
endfunction


" ============================
" Commands
" ============================
command! SpeakChar call SpeakChar()
command! SpeakWord call SpeakWord()
command! SpeakPos call SpeakPos()

command! SpeakBuffer call SpeakBufferName() 

" ============================
" Key mappings
" ============================
" Remap next/prev search keys
nnoremap n n:call SpeakSearchCountForKey()<CR>
nnoremap N N:call SpeakSearchCountForKey()<CR>
nnoremap <M-c> :SpeakChar<CR>
nnoremap <M-w> :SpeakWord<CR>
nnoremap <M-f> :SpeakPos<CR>
nnoremap <M-m> :call ReadLastMessage()<CR>
nnoremap <M-d> :echom system('date') <CR>

nnoremap <M-s> :silent .write !festival --tts<CR>
nnoremap <M-S> :silent execute 'silent !echo line ' . line('.') . " \| festival --tts"<CR>

vnoremap <M-y> :silent '<,'>write !xsel -b<CR>
nnoremap <M-y> :silent .write !xsel -b<CR>
vnoremap <M-p> :silent '<,'>read !xsel -b<CR>
nnoremap <M-p> :silent .read !xsel -b<CR>
vnoremap <M-P> :silent '<,'>read !xsel<CR>
nnoremap <M-P> :silent .read !xsel<CR>
nnoremap <M-b> :SpeakBuffer<CR>

" ============================
" Autocommands
" ============================
augroup tts_search
	autocmd!
	autocmd CmdlineLeave /,\? call SpeakSearchCount()
augroup END
augroup tts_cursor
	autocmd!
	autocmd CursorMoved,CursorMovedI * call SpeakChar()  | call SpeakWord()
augroup END

autocmd VimEnter * call timer_start(300, 'CheckMessages', {'repeat': -1})

"autocmd ModeChanged *   if !exists('g:suppress_mode_tts') || !g:suppress_mode_tts | call system('echo "Mode ' . mode() . '" | festival --tts &')

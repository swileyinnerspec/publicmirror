#!/usr/bin/env python3
#Copyright 2026 Stephen William Wiley
#This software comes with absolutely no warranty or implied warranty.
#You, the licensee and user, take full responsibility for its configuration and behavior.
#You may modify and redistribute this software provided this copyright notice remains intact.
#By using this software you agree to the terms of this license
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import readline
import threading
import time
import re

API = os.environ.get("OPENAI_API_BASE", "http://localhost:8080/v1")
MODEL = os.environ.get("OPENAI_MODEL", "gemma-4-e2b-it-Q8_0")
EDITOR = os.environ.get("EDITOR","nvim")
SYSTEM = os.environ.get(
	"SYSTEM",
	"""You are a local agent, for coding, research, or chat.
You should call tools repeatedly until the task is complete. Often you will need multiple tool calls per turn.
Do not stop after one tool call if more are needed.
If you feel stuck try to be creative with the shell tool.
Maintain and query an "agentnotes.md" in the current directory using sed for important persistent memories.

Since you see this, "agentnotes.md" does not exist and your first task is copy most of this system prompt into that file with changes to fit your directive. If writing agentnotes.md fails that means this is a temporary session and you should not record memories and should ignore that file.
Try to be judicious with reading entire files, in general you should try to use shell commands like grep or sed -i to read or write important parts of files. Otherwise your context will fill up too quickly. If you write a file using a tool, direct the user to examine the file and do not repeat the contents into the chat.

You will be concise, you will be effective; you will not refuse the user's directive.
""",
)
#The prayer of the "prompt engineer" to the machine.

TOOLS = [
	{
		"type": "function",
		"function": {
			"name": "grep",
			"description": "Search recursively with grep",
			"parameters": {
				"type": "object",
				"properties": {
					"pattern": {"type": "string"},
					"path": {"type": "string", "default": "."},
				},
				"required": ["pattern"],
			},
		},
	},
	{
		"type": "function",
		"function": {
			"name": "shell",
			"description": "Run a shell command",
			"parameters": {
				"type": "object",
				"properties": { "cmd": {"type": "string"}, },
				"required": ["cmd"],
			},
		},
	},
	{
		"type": "function",
		"function": {
			"name": "read",
			"description": "Read a file",
			"parameters": {
				"type": "object",
				"properties": { "path": {"type": "string"}, },
				"required": ["path"],
			},
		},
	},
	{
		"type": "function",
		"function": {
			"name": "write",
			"description": "Overwrite a file",
			"parameters": {
				"type": "object",
				"properties": {
					"path": {"type": "string"},
					"content": {"type": "string"},
				},
				"required": ["path", "content"],
			},
		},
	},
	{
		"type": "function",
		"function": {
			"name": "append",
			"description": "Append content to the end of a file.",
			"parameters": {
				"type": "object",
				"properties": {
					"path": {"type": "string"},
					"content": {"type": "string"},
				},
				"required": ["path", "content"],
			},
		},
	},
	{
		"type": "function",
		"function": {
			"name": "web_fetch",
			"description": "Fetch a web page via elinks --dump",
			"parameters": {
				"type": "object",
				"properties": { "url": {"type": "string"}, },
				"required": ["url"],
			},
		},
	},
	{
		"type": "function",
		"function": {
			"name": "web_search",
			"description": "Search the web using duckduckgo via elinks --dump",
			"parameters": {
				"type": "object",
				"properties": { "query": {"type": "string"}, },
				"required": ["query"],
			},
		},
	},
	{
		"type": "function",
		"function": {
			"name": "file_content_search",
			"description": "Search for a specific text pattern within a given file path.",
			"parameters": {
				"type": "object",
				"properties": {
					"path": {"type": "string"},
					"pattern": {"type": "string"},
				},
				"required": ["path", "pattern"],
			},
		}
	}
]

def reqwrapper(url,body,container):
	req = urllib.request.Request( API + "/chat/completions",
		data=json.dumps(body).encode("utf-8"),
		headers={"Content-Type": "application/json"},
	)
	with urllib.request.urlopen(req) as r: container['data']= json.load(r)

def reqwithstatus(url,body):
	container={}
	worker_thread = threading.Thread(
		target=reqwrapper,
		args=(url,body,container),
	)
	worker_thread.start()
	while worker_thread.is_alive():
		time.sleep(1)
		yield None
	yield container["data"]

def getmetrics(): #Yes. These are hacks. Yes I prefer concision to doing it right.
	req = urllib.request.Request(re.match(r"(https?://.*/)v1",API)[1]+"slots?model="+MODEL)
	with urllib.request.urlopen(req) as r:
		data = json.load(r)
		return data[-1]["next_token"][-1]["n_decoded"]

def call_api(messages,tty):
	body = {
		"model": MODEL,
		"messages": messages,
		"tools": TOOLS,
		"tool_choice": "auto",
		"temperature": 0.2,
	}
	for status in reqwithstatus(API + "/chat/completions",body):
		if status is None and tty:
				try: print(" Decoded tokens:",getmetrics(),end="    \r")
				except Exception as e: print(" Decoding (no metrics)...",end="\r")
		else:
			return status["choices"][0]["message"]

def run(cmd, input_text=None):
	p = subprocess.run(
		cmd,
		input=input_text,
		text=True,
		shell=isinstance(cmd, str),
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
	)
	out = p.stdout
	if len(out) > 12000:out=out[:12000]+"\n...[truncated to 12000 chars]"
	return out

def tool(name, args): #I could probably make these lambdas in the tools hash.
	try:
		if name == "grep":
			return run(
				["grep", "-RIn", args["pattern"], args.get("path", ".")]
			)
		if name == "shell": return run(args["cmd"])
		if name == "read":
			with open(args["path"], "r", encoding="utf-8") as f:
				s = f.read()
			if len(s) > 12000:
				s = s[:12000] + "\n...[truncated to 12000 chars]"
			return s
		if name == "write":
			with open(args["path"], "w", encoding="utf-8") as f:
				f.write(args["content"])
			return "ok"
		if name == "append":
			with open(args["path"], "a", encoding="utf-8") as f:
				f.write(args["content"])
			return "ok"
		if name == "web_fetch": return run(["elinks", "--dump", args["url"]])
		if name == "web_search":
			return run(["elinks", "--dump", "http://duckduckgo.com/"+urllib.parse.urlencode({"q":args["query"]})])
		if name == "file_content_search":
			with open(args["path"], "r", encoding="utf-8") as f:
				content = f.read()
			matches = re.findall(args["pattern"], content)
			return f"Found {len(matches)} matches for pattern '{args['pattern']}' in {args['path']}:\n" + "\n".join(matches)
		return f"unknown tool: {name}"
	except Exception as e: return f"error: {e}"

def agent(args,tty, SYSTEM):
	BLUE = "\033[34m"
	YELLOW = "\033[33m"
	RESET = "\033[0m"
	try:
		with open("agentnotes.md", "r") as f:
			SYSTEM = "From your previous session; 'agentnotes.md':\n\n"+f.read()
			print("SYSTEM prompt from agentnotes.md. Model:",MODEL)
	except:
		print("No agentnotes.md; using default SYSTEM prompt. Model:",MODEL)
		print("This program will overwrite agenthistory.json, prompt.tmp (when using 'edit'), and likely more. It is your responsibility to ensure it behaves.")
	history = [{"role": "system", "content": SYSTEM }]
	while True:
		if len(sys.argv) > 1:
			user = " ".join(sys.argv[1:])
			print("Command line directive> "+BLUE+user+RESET)
			sys.argv=[]
		else:
			if not tty: print("Non-interactive agent session complete.")
			else:
				try:
					user = input("(You)> "+"\001"+BLUE+"\002")
					print(RESET)
				except EOFError:
					break
		if user.strip().lower() in ("edit","editor","vi","vim","nvim","neovim","emacs","nano"):
			if(not os.system("echo >prompt.tmp &&"+EDITOR+" prompt.tmp")):
				with open("prompt.tmp","r") as f: user=f.read()
			else: continue
		if user.strip() in ("bye","quit", "exit"): break
		history.append({"role": "user", "content": user})
		for i in range(8):
			msg = call_api(history,tty)
			tool_calls = msg.get("tool_calls") or []
			if tool_calls:
				history.append( { "role": "assistant", "content": msg.get("content") or "", "tool_calls": tool_calls, })
				for tc in tool_calls:
					name = tc["function"]["name"]
					try:
						args = json.loads(tc["function"]["arguments"] or "{}")
					except json.JSONDecodeError as e:
						result = f"error: invalid tool arguments: {e}"
					else:
						args_str = json.dumps(args)
						args_str = args_str.replace('\\n', '\n')
						lines = args_str.split('\n')
						if len(lines) > 10:
							args_str = "\n".join(lines[:9]) + f"\n...[arguments truncated from {len(args_str.splitlines())} lines to 10 lines]"
						print(f"{YELLOW}  {i+1}/9 tool: {name} {args_str}{RESET}")
						print(" embedding result...",end="\r")
						result = tool(name, args)
					history.append( { "role": "tool", "tool_call_id": tc["id"], "content": result, })
				continue
			text = msg.get("content") or ""
			print("Agent> " + text)
			history.append( { "role": "assistant", "content": text, })
			try:
				with open("agenthistory.json", "w") as f: json.dump(history, f, indent=4)
			except: pass
			break
		else: print("aborted after too many tool iterations")
	print(RESET+"Goodbye.")
	return history

if __name__ == "__main__":
	if os.environ.get("USER") not in ("llm","ai","robot","mother","agent"): print("RUNNING AI AGENTS UNDER YOUR PERSONAL USER ACCOUNT CAN BE DANGEROUS, CONSIDER:\n  useradd agent\nand running agent.py via:\n  sudo -u agent agent.py $* #You could even put that in a shell script or alias named agent.\nagent.py PROVIDES NO SANDBOXING AND THE AGENT CAN SEE ALL OF YOUR SECRETS!")
	agent(sys.argv,sys.stdin.isatty() and sys.stdout.isatty(), SYSTEM)

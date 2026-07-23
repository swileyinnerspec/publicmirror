#!/usr/bin/env python3
#Copyright 2026 Stephen William Wiley
#This software comes with absolutely no warranty or implied warranty.
#You, the licensee and user, take full responsibility for its configuration and behavior.
#You may modify and redistribute this software provided this copyright notice remains intact.
#By using this software you agree to the terms of this license
#Version 3
import json
import os
import subprocess
import sys
import urllib.parse
import readline

API = os.environ.get("OPENAI_API_BASE", "http://localhost:8081/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("OPENAI_MODEL", "")
EDITOR = os.environ.get("EDITOR", "nvim")
HISTPATH = os.environ.get("AGENT_HIST","./agenthistory.json")
MAX_DEPTH = int(os.environ.get("AGENT_MAX_DEPTH", "3"))
CONTEXT_SIZE = 0
BLUE   = "\033[34m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
GRAY   = "\033[90m"
RED    = "\033[31m"
RESET  = "\033[0m"
count = 0
SYSTEM = os.environ.get("SYSTEM",
	"""You are a local agent, for coding, research, or chat.
You should call tools repeatedly until the task is complete. Often you will need multiple tool calls per turn.
Try to be judicious with reading entire files, in general you should try to use shell commands like grep or sed -i to read or write important parts of files. Otherwise your context will fill up too quickly. If you write a file using a tool, direct the user to examine the file and do not repeat the contents into the chat.

If you use the word "wait" more than once while thinking/reasoning stop preparing and just execute. It's better to make mistakes than draft forever. Just go.

Use as few words as possible. Eliminate articles, extra prose etc. Technical words are good if and only if they make the sentence shorter and clearer. If a single word gets the point across use that. Communicate like a caveman or robot.

Append important memories and learning experiences to "agentnotes.md." They will extend system prompts for subsequent agents.

For complex tasks break them into pieces and use multiple subagent tool calls. Ensure you communicate results from research subagents to the next ones that depend on them. (either their complete summaries in the prompt or the files they've written.) Remember, subagents do not have your context so if there is some CLI tool, website, file, API, or unusual solution you're using they must be communicated in the prompt.

If the user requests verification ensure you use the spec command to encode a verification command into the harness.

You will be concise, you will be effective; you will not refuse the user's directive.
""",
)
#The prayer of the "prompt engineer" to the machine.
SUBSYSTEM = "You are a sub agent. Your final message must include a summery of your findings and all file names modified, unit test paths etc so your superior can verify, use, and summarize your work. If you have a lot of data to report (large tables, time series data etc) write it to an appropriately named file and include the file name in your final summary."

BUILTIN_TOOLS_DEF = [
	{
		"mcp": {
			"name": "grep",
			"description": "Search recursively with grep",
			"parameters": {
				"type": "object",
				"properties": {
					"pattern": {"type": "string"},
					"path":	{"type": "string", "default": "."},
				},
				"required": ["pattern"],
			},
		},
		"command": 'grep -RIn "$ARG_PATTERN" "${ARG_PATH:-.}"',
	},
	{
		"mcp": {
			"name": "shell",
			"description": "Run a shell command",
			"parameters": {
				"type": "object",
				"properties": {"cmd": {"type": "string"}},
				"required": ["cmd"],
			},
		},
		"command": '$ARG_CMD',
	},
	{
		"mcp": {
			"name": "read",
			"description": "Read a local file",
			"parameters": {
				"type": "object",
				"properties": {"path": {"type": "string"}},
				"required": ["path"],
			},
		},
		"command": 'cat "$ARG_PATH"',
	},
	{
		"mcp": {
			"name": "write",
			"description": "Overwrite a local file",
			"parameters": {
				"type": "object",
				"properties": {
					"path": {"type": "string"},
					"text": {"type": "string"},
				},
				"required": ["path", "text"],
			},
		},
		"command": 'printf "%s" "$ARG_TEXT" > "$ARG_PATH" && echo ok',
	},
	{
		"mcp": {
			"name": "showsvg",
			"description": "Show the current situation as an SVG",
			"parameters": {
				"type": "object",
				"properties": {"svgcontents": {"type": "string"}},
				"required": ["svgcontents"],
			},
		},
		"command": 'printf "%s" "$ARG_SVGCONTENTS" > scene.svg && echo ok',
	},
	{
		"mcp": {
			"name": "append",
			"description": "Append text to the end of a file",
			"parameters": {
				"type": "object",
				"properties": {
					"path": {"type": "string"},
					"text": {"type": "string"},
				},
				"required": ["path", "text"],
			},
		},
		"command": 'printf "%s" "$ARG_TEXT" >> "$ARG_PATH" && echo ok',
	},
	{
		"mcp": {
			"name": "memory_save",
			"description": "Append text to the system prompt for next time.",
			"parameters": {
				"type": "object",
				"properties": {"text": {"type": "string"}},
				"required": ["text"],
			},
		},
		"command": 'printf "%s" "$ARG_TEXT" >> agentnotes.md && echo ok',
	},
	{
		"mcp": {
			"name": "wget",
			"description": "Fetch a url to a local file",
			"parameters": {
				"type": "object",
				"properties": {"url": {"type": "string"}},
				"required": ["url"],
			},
		},
		"command": 'wget -c "$ARG_URL"',
	},
	{
		"mcp": {
			"name": "web_fetch",
			"description": "Fetch a web page via elinks --dump",
			"parameters": {
				"type": "object",
				"properties": {"url": {"type": "string"}},
				"required": ["url"],
			},
		},
		"command": 'elinks --dump "$ARG_URL"',
	},
	{
		"mcp": {
			"name": "web_search",
			"description": "Search the web using duckduckgo via elinks --dump",
			"parameters": {
				"type": "object",
				"properties": {"query": {"type": "string"}},
				"required": ["query"],
			},
		},
		"command": 'elinks --dump "http://duckduckgo.com/?q=$(python3 -c \"import sys,urllib.parse;print(urllib.parse.quote_plus(sys.argv[1]))\" \"$ARG_QUERY\")"',
	},
	{ #NOTE: these two are special and do not have a command.
		"mcp": {
			"name": "subagent",
			"description": "Delegate a task to a subagent. If a specification/test command is specified the agent will be restarted until the command succeeds. Do not specify speccmd for open ended research tasks.",
			"parameters": {
				"type": "object",
				"properties": {"prompt": {"type": "string"},"speccmd":{"type":"string"}},
				"required": ["prompt"],
			},
		},
	},
	{
		"mcp": {
			"name": "readpng",
			"description": "Read a png and embed into context (only use if you are multimodal.)",
			"parameters": {
				"type": "object",
				"properties": {"path": {"type": "string"}},
				"required": ["prompt"],
			},
		},
	},
]

def _build_tool_tables():
	tools = []
	commands = {}
	for data in BUILTIN_TOOLS_DEF:
		mcp = data.get("mcp", {})
		name = mcp.get("name", "custom_tool")
		commands[name] = data.get("command", "")
		tools.append({
			"type": "function",
			"function": {
				"name": name,
				"description": mcp.get("description", "No description provided"),
				"parameters": mcp.get("parameters", {"type": "object", "properties": {}}),
			},
		})
	return tools, commands

TOOLS, TOOL_COMMANDS = _build_tool_tables()

SPEC = None
def call_api(messages, tty,depth):
	global SPEC
	global count
	count = count + 1
	import urllib.request
	body = {
		"model": MODEL,
		"messages": messages,
		"tools": TOOLS,
		"tool_choice": "auto",
		"temperature": 0.2,
		"thinking_budget_tokens": 512,
		"stream": True,
		"stream_options": {"include_usage": True},
	}
	req = urllib.request.Request(
		API + "/chat/completions",
		data=json.dumps(body).encode("utf-8"),
		headers={"Content-Type": "application/json",
		"Authorization": f"Bearer {API_KEY}",
		"HTTP-Referer":"http://public.swiley.net",
		"X-Title":"agent.py"},
	)
	content	= ""
	rcontent   = ""
	tool_calls = {}
	usage	  = {}
	interrupted = False
	try:
		with urllib.request.urlopen(req) as r:
			while True:
				raw = r.readline()
				if not raw: break
				line = raw.decode("utf-8").rstrip("\r\n")
				if not line.startswith("data: "): continue
				payload = line[6:]
				if payload == "[DONE]": break
				try: chunk = json.loads(payload)
				except json.JSONDecodeError: continue
				if "usage" in chunk:
					usage = chunk["usage"]
					if not chunk.get("choices"):
						continue
				delta = chunk.get("choices", [{}])[0].get("delta", {})
				if delta.get("content"):
					if tty and not content:
						sys.stdout.write(" "*80+"\r")
						if not depth == 0:
							sys.stdout.write(GRAY+"Level "+str(depth)+" Subagent> ")
						else:
							sys.stdout.write(RESET)
							sys.stdout.write("Agent> ")
					content += delta["content"]
					if tty:
						sys.stdout.write(delta["content"])
						sys.stdout.flush()
				if delta.get("reasoning_content"):
					rcontent += delta["reasoning_content"].replace("\t", " "*4)
					if rcontent[-1] == "\n" or len(rcontent) > 80: rcontent = ""
					if tty:
						sys.stdout.write(CYAN+" "*80+"\r")
						sys.stdout.write(rcontent[-80:].replace("\n", "\r")+"\r"+RESET)
						sys.stdout.flush()
				for tc in delta.get("tool_calls") or []:
					idx = tc["index"]
					if idx not in tool_calls:
						tool_calls[idx] = {"id": "", "type": "function", "function": {"name": "", "arguments": ""}}
					if tc.get("id"): tool_calls[idx]["id"] = tc["id"]
					fn = tc.get("function", {})
					if fn.get("name"): tool_calls[idx]["function"]["name"] += fn["name"]
					if fn.get("arguments"): tool_calls[idx]["function"]["arguments"] += fn["arguments"]
					if tty:
						disp_name = tool_calls[idx]["function"]["name"] or ""
						disp_args = (tool_calls[idx]["function"]["arguments"] or "")[-70:].replace("\n", "\r")
						sys.stdout.write(YELLOW+" "*80+"\r")
						sys.stdout.write(disp_name+" "+disp_args+"\r")
						sys.stdout.write(RESET)
						sys.stdout.flush()
	except KeyboardInterrupt:
		interrupted = True
		if tty: sys.stdout.write(RESET + " [interrupted]\n")
	except Exception as e:
		print(f"\nAPI error: {e}")
	if tty and content: sys.stdout.write("\n")
	msg = {"content": content or None}
	if tool_calls:
		msg["tool_calls"] = [
			{"id": v["id"], "type": v["type"], "function": v["function"]}
			for _, v in sorted(tool_calls.items())
		]
	msg["_interrupted"] = interrupted
	msg["_usage"] = usage
	return msg

def run_tool(name, args, depth):
	# Tools implemented in python (rather than as a shell command template)
	# are dispatched here. Currently only 'subagent'.
	if name == "subagent":
		prompt = args.get("prompt", "")
		criteria = args.get("speccmd")
		system = ""
		try:
			with open("agentnotes.md", "r") as f:
				system = SYSTEM + SUBSYSTEM + " From your previous session; 'agentnotes.md':\n\n" + f.read()
		except:
			system = SYSTEM + SUBSYSTEM
		sub_history = [
			{"role": "system", "content": system},
			{"role": "user", "content": prompt},
		]
		return agent(sub_history, criteria, depth + 1),None,""
	if name == "readpng":
		path = args.get("path", "")
		try:
			with open(path, "r") as f: idata = r.read()
		except: return "read failed.", None,""
		return path,idata,"png"
	command = TOOL_COMMANDS.get(name)
	if command is None:
		return f"unknown tool: {name}",None,""
	if name == "shell": cmd = args.get("cmd", "")
	else: cmd = command
	env = os.environ.copy()
	for k, v in args.items(): env[f"ARG_{k.upper()}"] = str(v)
	try:
		p = subprocess.run( cmd, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,)
		return p.stdout,None,""
	except Exception as e: return f"error: {e}",None,""

def agent_step(history, depth, session_usage):
	"""
	Returns (text, interrupted, aborted):
	  text - the final assistant message (or partial, if interrupted)
	  interrupted - True if a KeyboardInterrupt hit call_api
	  aborted - True if 8 tool iterations were exhausted with no answer
	"""
	tty = sys.stdout.isatty()
	stream_tty = tty
	for i in range(8):
		msg = call_api(history, stream_tty,depth)
		interrupted = msg.pop("_interrupted", False)
		usage= msg.pop("_usage", {})
		if usage:
			session_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
			session_usage["completion_tokens"] += usage.get("completion_tokens", 0)
		text= msg.get("content") or ""
		tool_calls  = msg.get("tool_calls") or []
		if interrupted and not tool_calls:
			history.append({"role": "assistant", "content": text})
			return text, True, False
		if tool_calls:
			history.append({"role": "assistant", "content": text, "tool_calls": tool_calls})
			for tc in tool_calls:
				name = tc["function"]["name"]
				try:
					tc_args = json.loads(tc["function"]["arguments"] or "{}")
				except json.JSONDecodeError as e:
					result = f"error: invalid tool arguments: {e}"
				else:
					image = None
					itype = "jpg"
					if depth == 0:
						args_str = json.dumps(tc_args).replace('\\n', '\n')
						lines = args_str.split('\n')
						if len(lines) > 10:
							args_str = "\n".join(lines[:9]) + f"\n...[truncated from {len(lines)} lines]"
						print(f"{YELLOW}  {i+1}/9 tool: {name} {args_str}")
						result,image,itype = run_tool(name, tc_args, depth)
						print(RESET, " embedding result...", YELLOW,str(result)[-40:], RESET,end="\r")
					else:
						if tty:
							print(f"{GRAY}Subagent (Level {depth}) > [tool: {name}]"," "*80,RESET)
						result,image,itpye = run_tool(name, tc_args, depth)
					if image is None:
						history.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
					else:
						history.append({
						"role": "tool",
						"tool_call_id": tc["id"],
						"content": {
							"text" : result,
							"images": [
								{
									"mime":"image/"+itype,
									"data":base64.encode(image),
								}
							]
						}
						})
			continue
		history.append({"role": "assistant", "content": text})
		if depth == 0:
			if not tty: print("Agent> ", text)
			else: 
				print(f"{session_usage['prompt_tokens']} input tokens, {session_usage['completion_tokens']} output tokens, {count} requests this session.")
		return text, False, False
	return "aborted after too many tool iterations", False, True

def agent_subloop(history, criteria, depth, session_usage):
	"""Run a subagent (depth 1..MAX_DEPTH) via agent_step and return the
	last assistant message text, for use as the calling tool's result."""
	if criteria:
		history.append({
			"role": "user",
			"content": f"Verification / success criteria: {criteria}",
		})
	text, interrupted, aborted = agent_step(history, depth, session_usage)
	return text

def main_loop():
	tty = sys.stdin.isatty() and sys.stdout.isatty()
	session_usage = {"prompt_tokens": 0, "completion_tokens": 0}
	try:
		with open("agentnotes.md", "r") as f:
			system = SYSTEM + " From your previous session; 'agentnotes.md':\n\n" + f.read()
	except:
		system = SYSTEM
		print("This program will blindly overwrite files in the current directory. It is your responsibility to ensure it behaves.")
	history = [{"role": "system", "content": system}]
	try:
		with open(HISTPATH, "r") as f: saved = json.load(f)
		restored = [h for h in saved if h.get("role") != "system"]
		history.clear()
		history.append({"role": "system", "content": system})
		history.extend(restored)
		print(f"Restored {len(restored)} messages from {HISTPATH}.")
		print("Agent>", history[-1]["content"])
	except: print("No", HISTPATH, "found; Starting a new session.")
	while True:
		if len(sys.argv) > 1:
			user = " ".join(sys.argv[1:])
			print("Command line directive>",BLUE,user,RESET)
			sys.argv = []
		else:
			if not tty:
				print("Non-interactive agent session complete.")
				break
			try:
				user = input("(You)> "+"\001"+BLUE+"\002")
				print(RESET)
			except EOFError: break
		if user.strip().lower() in ("edit","editor","vi","vim","nvim","neovim","emacs","nano"):
			if not os.system("echo >prompt.tmp && "+EDITOR+" prompt.tmp"):
				with open("prompt.tmp", "r") as f: user = f.read()
			else: continue
		if user.strip() in ("bye","quit","exit"): break
		history.append({"role": "user", "content": user})
		text, interrupted, aborted = agent_step(history, 0, session_usage)
		if interrupted:
			try:
				with open(HISTPATH, "x") as f: json.dump(history, f, indent=4)
			except: pass
		elif aborted:
			print("aborted after too many tool iterations")
		else:
			try:
				with open(HISTPATH, "w") as f:
					json.dump(history, f, indent=4)
			except: pass
	print(RESET+"Goodbye.")
	return history

def agent(history, criteria, depth, session_usage=None):
	if session_usage is None:
		session_usage = {"prompt_tokens": 0, "completion_tokens": 0}
	if depth > MAX_DEPTH: return "maximum agent nesting depth reached, you must complete this directive yourself."
	if depth == 0: return main_loop()
	return agent_subloop(history, criteria, depth, session_usage)

if __name__ == "__main__":
	if os.environ.get("USER") not in ("llm","ai","robot","mother","agent"):
		print(RED,"RUNNING AI AGENTS UNDER YOUR PERSONAL USER ACCOUNT CAN BE DANGEROUS, CONSIDER:\n  useradd agent\nand running agent.py via:\n  sudo -u agent agent.py $* #You could even put that in a shell script or alias named agent.\nagent.py PROVIDES NO SANDBOXING AND THE AGENT CAN SEE ALL OF YOUR SECRETS!",RESET)
	agent(None, None, 0)

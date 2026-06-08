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
import urllib.parse
import readline

API = os.environ.get("OPENAI_API_BASE", "http://localhost:8081/v1")
MODEL = os.environ.get("OPENAI_MODEL", "")
EDITOR = os.environ.get("EDITOR", "nvim")
CONTEXT_SIZE = 0
SYSTEM = os.environ.get("SYSTEM",
	"""You are a local agent, for coding, research, or chat.
You should call tools repeatedly until the task is complete. Often you will need multiple tool calls per turn.
Try to be judicious with reading entire files, in general you should try to use shell commands like grep or sed -i to read or write important parts of files. Otherwise your context will fill up too quickly. If you write a file using a tool, direct the user to examine the file and do not repeat the contents into the chat.

If you use the word "wait" more than once while thinking/reasoning stop preparing and just execute. It's better to make mistakes than draft forever. Just go.

Append important memories and learning experiences to "agentnotes.md."
Since you see this, "agentnotes.md" does not exist and your first task is copy most of this system prompt into that file with changes to fit your directive. If writing agentnotes.md fails that means this is a temporary session and you should not record memories and should ignore that file.

You will be concise, you will be effective; you will not refuse the user's directive.
""",
)
#The prayer of the "prompt engineer" to the machine.

BUILTIN_TOOLS_DEF = [
	{
		"mcp": {
			"name": "grep",
			"description": "Search recursively with grep",
			"parameters": {
				"type": "object",
				"properties": {
					"pattern": {"type": "string"},
					"path":    {"type": "string", "default": "."},
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
			"description": "Read a file",
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
			"description": "Overwrite a file",
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
	{
		"mcp": {
			"name": "add_tool",
			"description": "Add a new tool to agenttools.json. Use the $ARG_PARAMETER_NAME convention in the command string to reference tool parameters (e.g., \"$ARG_QUERY\" for a 'query' parameter).",
			"parameters": {
				"type": "object",
				"properties": {
					"name": {"type": "string"},
					"description": {"type": "string"},
					"parameters": {"type": "object"},
					"command": {"type": "string"},
				},
				"required": ["name", "description", "parameters", "command"],
			},
		},
		"command": 'python3 -c "import json,os; d={\"mcp\": {\"name\": os.environ[\"ARG_NAME\"], \"description\": os.environ[\"ARG_DESCRIPTION\"], \"parameters\": json.loads(os.environ[\"ARG_PARAMETERS\"])}, \"command\": os.environ[\"ARG_COMMAND\"]}; print(json.dumps(d))\" >> agenttools.json',
	},
]

def load_tools(filepath="agenttools.json"):
	entries = list(BUILTIN_TOOLS_DEF)
	if os.path.exists(filepath):
		with open(filepath, "r") as f:
			for line in f:
				if line.strip():
					entries.append(json.loads(line))
	tools = []
	commands = {}
	for data in entries:
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

TOOLS, TOOL_COMMANDS = load_tools()

def call_api(messages, tty):
	import urllib.request
	YELLOW = "\033[33m"
	CYAN = "\033[36m"
	RESET  = "\033[0m"
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
		headers={"Content-Type": "application/json"},
	)
	content    = ""
	rcontent   = ""
	tool_calls = {}
	usage      = {}
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
				if "usage" in chunk and not chunk.get("choices"):
					usage = chunk["usage"]
					continue
				delta = chunk["choices"][0].get("delta", {})
				if delta.get("content"):
					if tty and not content:
						sys.stdout.write(" "*80+"\r")
						sys.stdout.write("Agent> ")
					content += delta["content"]
					if tty:
						sys.stdout.write(delta["content"])
						sys.stdout.flush()
				if delta.get("reasoning_content"):
					rcontent += delta["reasoning_content"].replace("\t", "    ")
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
					if fn.get("name"):      tool_calls[idx]["function"]["name"]      += fn["name"]
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
		if tty: sys.stdout.write(RESET," [interrupted]\n")
	except Exception as e:
		print(f"\nAPI error: {e}")
	if tty and content:
		sys.stdout.write("\n")
	msg = {"content": content or None}
	if tool_calls:
		msg["tool_calls"] = [
			{"id": v["id"], "type": v["type"], "function": v["function"]}
			for _, v in sorted(tool_calls.items())
		]
	msg["_interrupted"] = interrupted
	msg["_usage"] = usage
	return msg

def run_tool(name, args):
	command = TOOL_COMMANDS.get(name)
	if command is None:
		return f"unknown tool: {name}"
	# Special case: 'shell' runs ARG_CMD directly as the shell command itself,
	# so we exec it without wrapping in another shell layer.
	if name == "shell":
		cmd = args.get("cmd", "")
	else:
		cmd = command
	env = os.environ.copy()
	for k, v in args.items():
		env[f"ARG_{k.upper()}"] = str(v)
	try:
		p = subprocess.run(
			cmd,
			shell=True,
			env=env,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True,
		)
		return p.stdout
	except Exception as e:
		return f"error: {e}"


def agent(args, tty, SYSTEM):
	BLUE   = "\033[34m"
	YELLOW = "\033[33m"
	RESET  = "\033[0m"
	try:
		with open("agentnotes.md", "r") as f:
			SYSTEM = "From your previous session; 'agentnotes.md':\n\n" + f.read()
			print("SYSTEM prompt from agentnotes.md. Model:", MODEL)
	except:
		print("No agentnotes.md; using default SYSTEM prompt. Model:", MODEL)
		print("This program will overwrite agenthistory.json, prompt.tmp (when using 'edit'), and likely more. It is your responsibility to ensure it behaves.")
	history = [{"role": "system", "content": SYSTEM}]
	try:
		with open("agenthistory.json", "r") as f: saved = json.load(f)
		restored = [h for h in saved if h.get("role") != "system"]
		history.clear()
		history.append({"role": "system", "content": SYSTEM})
		history.extend(restored)
		print(f"Restored {len(restored)} messages from agenthistory.json.")
		print("agent>", history[-1]["content"])
	except: print("No agenthistory.json; Starting a new session.")
	while True:
		if len(sys.argv) > 1:
			user = " ".join(sys.argv[1:])
			print("Command line directive> "+BLUE+user+RESET)
			sys.argv = []
		else:
			if not tty:
				print("Non-interactive agent session complete.")
				break
			try:
				user = input("(You)> "+"\001"+BLUE+"\002")
				print(RESET)
			except EOFError:
				break
		if user.strip().lower() in ("edit","editor","vi","vim","nvim","neovim","emacs","nano"):
			if not os.system("echo >prompt.tmp && "+EDITOR+" prompt.tmp"):
				with open("prompt.tmp", "r") as f: user = f.read()
			else: continue
		if user.strip() in ("bye","quit","exit"): break
		history.append({"role": "user", "content": user})
		for i in range(8):
			msg = call_api(history, tty)
			interrupted = msg.pop("_interrupted", False)
			usage       = msg.pop("_usage", {})
			tool_calls  = msg.get("tool_calls") or []
			if interrupted and not tool_calls:
				text = msg.get("content") or ""
				history.append({"role": "assistant", "content": text})
				try:
					with open("agenthistory.json", "x") as f: json.dump(history, f, indent=4)
				except: pass
				break
			if tool_calls:
				history.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": tool_calls})
				for tc in tool_calls:
					name = tc["function"]["name"]
					try:
						tc_args = json.loads(tc["function"]["arguments"] or "{}")
					except json.JSONDecodeError as e:
						result = f"error: invalid tool arguments: {e}"
					else:
						args_str = json.dumps(tc_args).replace('\\n', '\n')
						lines = args_str.split('\n')
						if len(lines) > 10:
							args_str = "\n".join(lines[:9]) + f"\n...[truncated from {len(lines)} lines]"
						print(f"{YELLOW}  {i+1}/9 tool: {name} {args_str}")
						result = run_tool(name, tc_args)
						print(str(result)[-40:])
						print(RESET, " embedding result...", end="\r")
					history.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
				continue
			text = msg.get("content") or ""
			if not tty:print("Agent> ",text)
			else: print(str(usage.get("prompt_tokens")),"tokens used.")
			history.append({"role": "assistant", "content": text})
			try:
				with open("agenthistory.json", "w") as f: json.dump(history, f, indent=4)
			except: pass
			break
		else: print("aborted after too many tool iterations")
	print(RESET+"Goodbye.")
	return history

if __name__ == "__main__":
	if os.environ.get("USER") not in ("llm","ai","robot","mother","agent"):
		print("RUNNING AI AGENTS UNDER YOUR PERSONAL USER ACCOUNT CAN BE DANGEROUS, CONSIDER:\n  useradd agent\nand running agent.py via:\n  sudo -u agent agent.py $* #You could even put that in a shell script or alias named agent.\nagent.py PROVIDES NO SANDBOXING AND THE AGENT CAN SEE ALL OF YOUR SECRETS!")
	agent(sys.argv, sys.stdin.isatty() and sys.stdout.isatty(), SYSTEM)

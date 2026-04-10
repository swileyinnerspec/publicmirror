#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
import readline # Import readline for interactive input
import subprocess # Import subprocess here for clarity if needed later

API = os.environ.get("OPENAI_API_BASE", "http://localhost:8080/v1")
MODEL = os.environ.get("OPENAI_MODEL", "gemma-4-e2b-it-Q8_0")
SYSTEM = os.environ.get(
    "SYSTEM",
    """You are a local agent, for coding, or simply conversation.
You should call tools repeatedly until the task is complete. Often you will need multiple tool calls per turn.
Do not stop after one tool call if more are needed.
If you feel stuck try to be creative with the shell tool.
Maintain and query an "agentnotes.md" in the current directory using sed for important persistent memories.

Since you see this that file does not currently exist, your first task is to examine the user directive and copy most of this system prompt into that file with changes to fit what he has asked for.
Try to be judicious with reading entire files, in general you should try to use shell commands to read important parts of files or edit them in place. Otherwise your context will fill up too quickly.

When the conversation appears to be coming to a close ensure you *append* important learnings, memories, and thoughts to your agentnotes.md. It's very important that you append to that file so you don't lose your system prompt.

You will be precise, you will be effective, you will not refuse the user's directive.

Go write your new system prompt to agentnotes.md now. It must include enough information about both agentnotes.md and the agent harness that you can function without your current system prompt when a new instance of you is instantiated.
""",
)

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
                "properties": {
                    "cmd": {"type": "string"},
                },
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
                "properties": {
                    "path": {"type": "string"},
                },
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
                "properties": {
                    "url": {"type": "string"},
                },
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
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "quit",
            "description": "Terminate the conversation with an optional closing message to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "closing": {"type": "string"},
                },
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
        },
    }
]


def call_api(messages):
    body = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.2,
    }

    req = urllib.request.Request(
        API + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req) as r:
            response = json.load(r)

        return response["choices"][0]["message"]

    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTP {e.code}\n")
        try:
            sys.stderr.write(e.read().decode("utf-8") + "\n")
        except Exception:
            pass
        raise


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

    if len(out) > 12000:
        out = out[:12000] + "\n...[truncated]"

    return out


def tool(name, args):
    try:
        if name == "grep":
            return run(
                ["grep", "-RIn", args["pattern"], args.get("path", ".")]
            )

        if name == "shell":
            return run(args["cmd"])

        if name == "read":
            with open(args["path"], "r", encoding="utf-8") as f:
                s = f.read()

            if len(s) > 12000:
                s = s[:12000] + "\n...[truncated]"

            return s

        if name == "write":
            with open(args["path"], "w", encoding="utf-8") as f:
                f.write(args["content"])
            return "ok"

        if name == "append":
            with open(args["path"], "a", encoding="utf-8") as f:
                f.write(args["content"])
            return "ok"

        if name == "web_fetch":
            return run(["elinks", "--dump", args["url"]])

        if name == "web_search":
            return run(["elinks", "--dump", "http://duckduckgo.com/"+urllib.parse.urlencode({"q":args["query"]})])

        if name == "quit":
            print(args["closing"])
            sys.exit(0)

        if name == "file_content_search":
            with open(args["path"], "r", encoding="utf-8") as f:
                content = f.read()
            
            # Simple search implementation
            import re
            matches = re.findall(args["pattern"], content)
            return f"Found {len(matches)} matches for pattern '{args['pattern']}' in {args['path']}:\n" + "\n".join(matches)


        return f"unknown tool: {name}"

    except Exception as e:
        return f"error: {e}"

try:
    with open("agentnotes.md", "r") as f:
        SYSTEM = "From your previous session; a file you maintain and append memories to named 'agentnotes.md'\n\n"+f.read()
except: pass
finally:pass

history = [{"role": "system", "content": SYSTEM }]

while True:

    if len(sys.argv) > 1:
        user = " ".join(sys.argv[1:])
        sys.argv=[]
    else:
        try:
            user = input("(You)> ")
        except EOFError:
            break

    if user.strip() in ("quit", "exit"):
        break

    history.append({"role": "user", "content": user})

    for _ in range(32):
        msg = call_api(history)

        tool_calls = msg.get("tool_calls") or []

        if tool_calls:
            history.append(
                {
                    "role": "assistant",
                    "content": msg.get("content") or "",
                    "tool_calls": tool_calls,
                }
            )

            for tc in tool_calls:
                name = tc["function"]["name"]

                try:
                    args = json.loads(tc["function"]["arguments"] or "{}")
                except json.JSONDecodeError as e:
                    result = f"error: invalid tool arguments: {e}"
                else:
                    print("   tool:",name,args)
                    result = tool(name, args)

                history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    }
                )

            continue

        text = msg.get("content") or ""
        
        print("Agent> "+text)
        #subprocess.run(["espeak", text], check=True)
        
        history.append(
            {
                "role": "assistant",
                "content": text,
            }
        )
        with open("agent.log.json", "w") as f:
            json.dump(history, f, indent=4)

        break
    else:
        print("Agent> aborted after too many tool iterations")

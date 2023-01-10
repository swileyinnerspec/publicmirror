#!/usr/bin/env python3
import sys
import os
import socket
path = "~/santa.sock"
os.remove(path)
checkpoint = "bigcode/santacoder"
device = "cpu" # for GPU usage or "cpu" for CPU usage
max_tokens=100
def serve(gen,path):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(path)
    os.chmod(path, 0777)
    sock.listen(1)
    print('listening on',path)
    while True:
        conn, addr = sock.accept()
        data = conn.recv(1024).decode()
        m = data.split(" ")[0]
        p = data.split(" ",1)[1]
        print(m,p)
        if m in gen:
            conn.send(gen[m](p).encode())
        else:
            con.send("no such model".encode())
        conn.close()

if len(sys.argv) == 2 and sys.argv[1] == "serve":
    print("loading flan-t5...");
    from transformers import T5Tokenizer, T5ForConditionalGeneration

    tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-xl")
    model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-xl").to("cpu")
    def flangen(input_text):
        if(len(input_text)>1):
            input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to("cpu")
            output = model.generate(input_ids, max_length=100)
            return tokenizer.decode(output[0], skip_special_tokens=True)
        else: return "no query"
    print("loading santa model...")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from transformers import logging
    logging.set_verbosity(logging.ERROR)
    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    model = AutoModelForCausalLM.from_pretrained(checkpoint, trust_remote_code=True).to(device)
    def santagen(s):
        if(len(s)>1):
            inputs = tokenizer.encode(s, return_tensors="pt").to(device)
            outputs = model.generate(inputs,max_new_tokens=max_tokens)
            return tokenizer.decode(outputs[0])
        else: return "no query"
    serve({"c":santagen,"q":flangen},path)
if len(sys.argv) == 1 or len(sys.argv) >3:
    print("\nUSAGE: santacoder serve|model [prompt]")
    print("Models:\n c: santacoder. Send a line for code\n q: Flan-t5-xxl: send a line for a thought.")
    print("serve will start the server listening on",path)
    print("from vim :.! santacoder c will complete your line\n")
else: 
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    con = sock.connect(path)
    p = sys.argv[2] if len(sys.argv) ==3 else input()
    p = sys.argv[1] + " " + p
    sock.send(p.encode())
    print(sock.recv(1024).decode())
    sock.close()

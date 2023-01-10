#!/usr/bin/env python3
#launch with santacoder.py serve
#To use from vim run :.!santacoder.py
import sys
import socket
path = "~/santa.sock"
#check if we're on host "stfrancis"
#open a unix domain socket and listen for connections
checkpoint = "bigcode/santacoder"
device = "cpu" # for GPU usage or "cpu" for CPU usage
max_tokens=100
def serve(gen,path):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(path)
    sock.listen(1)
    print('listening on',path)
    while True:
        conn, addr = sock.accept()
        data = conn.recv(1024).decode()
        print(data)
        conn.send(gen(data).encode())
        conn.close()

if len(sys.argv) > 1 and sys.argv[1] == "serve":
    print("loading model...")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from transformers import logging
    logging.set_verbosity(logging.ERROR)
    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    model = AutoModelForCausalLM.from_pretrained(checkpoint, trust_remote_code=True).to(device)
    def gen(s):
        if(len(s)>1):
            inputs = tokenizer.encode(s, return_tensors="pt").to(device)
            outputs = model.generate(inputs,max_new_tokens=max_tokens)
            #print(tokenizer.decode(outputs[0]))
            return tokenizer.decode(outputs[0])
        else: return "no query"
    serve(gen,path)

else:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    con = sock.connect(path)
    sock.send(input().encode())
    print(sock.recv(1024).decode())
    sock.close()

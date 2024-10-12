#standard network REPL
import network
import socket
import time
import os

# Define your network credentials
ssid = 'swiley.net'
password = 'kaboom3264!'

# Create a WiFi station object
station = network.WLAN(network.STA_IF)

# Activate the network interface
station.active(True)

# Connect to the network
station.connect(ssid, password)

# Wait for connection
while not station.isconnected():
	print("Connecting to WiFi...")
	time.sleep(1)

print("Connection successful!")
print("Network config:", station.ifconfig())

# Define TCP server parameters
HOST = ''       # Bind to all interfaces
PORT = 23       # Standard telnet port (you can change this)

def acc(server_socket):
	conn, addr = server_socket.accept()
	print(f"Connection from {addr}")
	conn.sendall(bytes([255, 252, 34])) # dont allow line mode
	conn.sendall(bytes([255, 251, 1])) # turn off local echo
	conn.write("hello\n")

	# Redirect REPL input/output to the connected socket
	os.dupterm(conn)

# Create a TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.setsockopt(socket.SOL_SOCKET, 20, acc)
server_socket.listen(1)


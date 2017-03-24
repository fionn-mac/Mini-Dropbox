import socket
import subprocess
import os
import os.path
import time
import threading
import sys
import hashlib
import struct
from stat import *

class autoSender(threading.Thread):
	def __init__(self, port):
		threading.Thread.__init__(self)
		self.port = port
		self.Socket = socket.socket()
		self.currentDir = os.curdir
		self.dlist = []
	
	def recieveAndWrite(self, args):
		with open('' + args, 'wb') as dFile:
			while True:
				data = self.Socket.recv(2048)
				if not data:
					break
				dFile.write(data)
			dFile.close()

	def download(self, args):
		if args[1] == "TCP":
			length = self.Socket.recv(4)
			length, = struct.unpack('I', length)
			fileInfo = self.Socket.recv(length).decode()
			temp = fileInfo.split()
			permissions = self.Socket.recv(2048)
			if temp[1] != "not":
				self.recieveAndWrite(args[2])
				subprocess.call(['chmod', permissions, args[2]])

	def indexing(self):
		allFiles = os.listdir(self.currentDir)
		amount = int(self.Socket.recv(4))
		time.sleep(0.1)
		for i in range(amount):
			data = self.Socket.recv(10000)
			if data not in allFiles:
				self.dlist.append(data)
	
	def hashVal(self, fileName):
		retVal = hashlib.md5()
		with open(fileName, "rb") as hashFile:
			for piece in iter(lambda: hashFile.read(4096), b""):
				retVal.update(piece)
		return retVal.hexdigest()
	
	def hashup(self):
		allFiles = os.listdir(self.currentDir)
		amount = int(self.Socket.recv(4))
		time.sleep(0.1)
		for i in range(amount):
			recieve = self.Socket.recv(10000)
			recieve = recieve.split()
			if recieve[0] in allFiles:
				thisHash = self.hashVal(recieve[0])
				if thisHash != recieve[1]:
					fileStat = os.stat(recieve[0])
					modTime = int(fileStat.st_mtime)
					if modTime < recieve[1]:
						self.dlist.append(recieve[0])
	
	def run(self):
		self.Socket = socket.socket()
		host = ""
		commands = ["index shortlist", "hash checkall", "download TCP "]
		while True:
			time.sleep(10)
			self.dlist = []
			for i in range(2):
				self.Socket = socket.socket()
				self.Socket.connect((host, self.port))
				self.Socket.send(commands[i])
				if i:
					self.hashup()
				else:
					self.indexing()
				
				self.Socket.close()
				time.sleep(0.1)
			
			for item in self.dlist:
				self.Socket = socket.socket()
				self.Socket.connect((host, self.port))
				command = commands[2] + item
				self.Socket.send(command)
				self.download(command.split())
				self.Socket.close()
				time.sleep(0.1)
		return
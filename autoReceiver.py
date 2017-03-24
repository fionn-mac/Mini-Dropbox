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

class autoReceiver (threading.Thread):
	def __init__(self, port):
		threading.Thread.__init__(self)
		self.port = port
		self.currentDir = os.curdir

	def hashVal(self, fileName):
		retVal = hashlib.md5()
		with open(fileName, "rb") as hashFile:
			for piece in iter(lambda: hashFile.read(4096), b""):
				retVal.update(piece)
		return retVal.hexdigest()

	def readAndSend(self, args, Connection):
		dFile = open('' + args, 'rb')
		piece = dFile.read(2048)
		while(piece):
			Connection.send(piece)
			piece = dFile.read(2048)
		dFile.close()
	
	def getFileInfo(self, args):
		fileStat = os.stat(args[2])
		retVal = args[2] + " " + str(fileStat.st_size) + " " + str(fileStat.st_mtime) + " " + self.hashVal(args[2])
		return bytes(retVal)
		
	def TCPDownload(self, args, Connection):
		fileInfo = self.getFileInfo(args)
		data = struct.pack("I%ds" % (len(fileInfo),), len(fileInfo), fileInfo)
		Connection.send(data)
		time.sleep(0.1)
		permissions = oct(os.stat(args[2])[ST_MODE])[-4:]
		Connection.send(str(permissions))
		time.sleep(0.1)
		self.readAndSend(args[2], Connection)

	def fileProperties(self, files):
		fileHash = self.hashVal(files)
		fileInfo = os.stat(files)
		modTime = int(fileInfo.st_mtime)
		return fileHash, modTime
	
	def shortlist(self, Connection):
		allFiles = os.listdir(self.currentDir)
		Connection.send(str(len(allFiles)))
		time.sleep(0.1)
		for files in allFiles:
			Connection.send(files)
			time.sleep(0.1)
			
	def checkall(self, Connection):
		allFiles = os.listdir(self.currentDir)
		Connection.send(str(len(allFiles)))
		time.sleep(0.1)
		for files in allFiles:
			fileHash, modTime = self.fileProperties(files)
			retval = files + " " + str(fileHash) + " " + str(modTime)
			Connection.send(retval)
			time.sleep(0.1)
	
	def run(self):
		Socket = socket.socket()
		host = ""
		Socket.bind((host, self.port))
		Socket.listen(5)

		while True:
			command = ''
			Connection, addr = Socket.accept()
			command = Connection.recv(2048)
			if command != '':
				args = command.split()
				
				if args[0] == "hash":
					if args[1] == "checkall":
						self.checkall(Connection)
				
				elif args[0] == "index":
					if args[1] == "shortlist":
						self.shortlist(Connection)

				elif args[0] == "download":
					if args[1] == "TCP":
						self.TCPDownload(args, Connection)
				
			Connection.close()

		Socket.close()
		return
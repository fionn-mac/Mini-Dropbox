import socket
import subprocess
import os
import os.path
import time
import threading
import sys
import hashlib
import select
import struct
from stat import *

class receiver(threading.Thread):
	def __init__(self, port):
		threading.Thread.__init__(self)
		self.port = port
		self.Socket = socket.socket()
		self.currentDir = os.curdir
	
	def getFileInfo(self, args):
		fileStat = os.stat(args[2])
		retVal = args[2] + " " + str(fileStat.st_size) + " " + str(fileStat.st_mtime) + " " + self.hashVal(args[2])
		return retVal
	
	def readAndSend(self, args, Connection):
		dFile = open('' + args[2], 'rb')
		piece = dFile.read(2048)
		while(piece):
			Connection.send(piece)
			piece = dFile.read(2048)
		dFile.close()
	
	def fileProperties(self, files):
		fileHash = self.hashVal(files)
		modTime = time.ctime(os.path.getmtime(files))
		return fileHash, modTime
	
	def listAndSend(self, listing, Connection):
		proc = subprocess.Popen(args = listing, stdout = subprocess.PIPE, shell = True)
		(retVal, err) = proc.communicate()
		Connection.send(retVal)
	
	def shortList(self, timeLower, timeUpper, Connection):
		allFiles = os.listdir(self.currentDir)
		fileList = []
		
		for files in allFiles:
			fileStat = os.stat(files)
			modTime = int(fileStat.st_mtime)
			if modTime <= timeUpper and modTime >= timeLower:
				fileList.append(files)
		
		Connection.send(str(len(fileList)))
		
		for files in fileList:
			listing = "ls -l " + files
			self.listAndSend(listing, Connection)
	
	def UDPDownload(self, args, Connection):
		UDPSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		host = ''
		bufferSize = 1024
		address = (host, self.port)
		fileName = args[2]
		fileHash = self.hashVal(args[2])
		UDPSocket.sendto(fileHash, address)
		time.sleep(0.1)
		UDPSocket.sendto(fileName, address)
		time.sleep(0.1)
		permissions = oct(os.stat(args[2])[ST_MODE])[-4:]
		Connection.send(str(permissions))
		UDPfile = open(fileName, "rb")
		time.sleep(0.1)
		piece = UDPfile.read(bufferSize)
		while(piece):
			if(UDPSocket.sendto(piece, address)):
				piece = UDPfile.read(bufferSize)
		UDPSocket.close()
		UDPfile.close()
		
	def TCPDownload(self, args, Connection):
		if os.path.exists(args[2]):
			fileInfo = self.getFileInfo(args)
			fileInfo = bytes(fileInfo)
			piece = struct.pack("I%ds" % (len(fileInfo),), len(fileInfo), fileInfo)
			Connection.send(piece)
			time.sleep(0.1)
			permissions = oct(os.stat(args[2])[ST_MODE])[-4:]
			Connection.send(str(permissions))
			time.sleep(0.1)
			self.readAndSend(args, Connection)
		
		else:
			message = "File not found"
			Connection.send(message)

	def hashVal(self, fileName):
		retVal = hashlib.md5()
		with open(fileName, "rb") as hashFile:
			for piece in iter(lambda: hashFile.read(4096), b""):
				retVal.update(piece)
		return retVal.hexdigest()

	def hashing(self, args, Connection):
		if args[1] == "checkall":
			allFiles = os.listdir(self.currentDir)
			Connection.send(str(len(allFiles)))
			for files in allFiles:
				fileHash, modTime = self.fileProperties(files)
				retVal = files + " " + str(fileHash) + " " + str(modTime)
				Connection.send(retVal)
		
		elif args[1] == "verify":
			if os.path.exists(args[2]):
				fileHash, modTime = self.fileProperties(args[2])
				retVal = str(fileHash) + " " + str(modTime)
				Connection.send(retVal)
			
			else:
				message = "File not found"
				Connection.send(message)
	
	def indexing(self, args, Connection):
		if args[1] == "longlist":
			listing = "ls -l"
			self.listAndSend(listing, Connection)
		
		elif args[1] == "shortlist":
			self.shortList(int(args[2]), int(args[3]), Connection)

		elif args[1] == "regex":
			listing = "ls -l | grep " + '"' + args[2] + '"'
			self.listAndSend(listing, Connection)
		
		else:
			print args[1] + ": Command not found"

	def run(self):
		host = ""
		self.Socket = socket.socket()
		self.Socket.bind((host, self.port))
		self.Socket.listen(5)

		while True:
			Connection, addr = self.Socket.accept()
			command = ''
			command = Connection.recv(2048)
			if command != '':
				args = command.split()
				if args[0] == "hash":
					self.hashing(args, Connection)
				
				elif args[0] == "index":
					self.indexing(args, Connection)

				elif args[0] == "download":
					if args[1] == "TCP":
						self.TCPDownload(args, Connection)
					elif args[1] == "UDP":
						self.UDPDownload(args, Connection)
					else:
						print args[1] + ": Command not found"
			
			Connection.close()

		self.Socket.close()
		return
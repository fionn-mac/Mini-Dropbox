import socket
import subprocess
import os
import os.path
import time
import threading
import sys
import hashlib
import struct
import select
from stat import *

class sender(threading.Thread):
	def __init__(self, port):
		threading.Thread.__init__(self)
		self.port = port
		self.Socket = socket.socket()
		self.UDPOngoing = False
		self.UDPFile = ""
	
	def getShortList(self):
		amount = int(self.Socket.recv(1000))
		for i in range(amount):
			data = self.Socket.recv(10000)
			print data

	def indexing(self, args):
		if args[1] == "regex" or args[1] == "longlist":
			data = self.Socket.recv(10000)
			print data
		
		elif args[1] == "shortlist":
			self.getShortList()
		
		else:
			print args[1] + ": Command not found"

	def hashup(self, args):
		if args[1] == "checkall":
			self.getShortList()
		
		elif args[1] == "verify":
			data = self.Socket.recv(1000)
			print data
		
		else:
			print args[1] + ": Command not found"

	def hashVal(self, fileName):
		retVal = hashlib.md5()
		with open(fileName, "rb") as hashFile:
			for piece in iter(lambda: hashFile.read(4096), b""):
				retVal.update(piece)
		return retVal.hexdigest()
	
	def UDPDownload(self, args):
			self.UDPOngoing = True
			self.UDPfile = args[2]
			host = ''
			UDPSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			UDPSocket.bind((host, self.port))
			address = (host, self.port)
			bufferSize = 1024
			newHash , address = UDPSocket.recvfrom(bufferSize)
			time.sleep(0.1)
			F, address = UDPSocket.recvfrom(bufferSize)

			print "Received File:", F.strip()
			UDPfile = open(F.strip(), 'wb')
			permissions = self.Socket.recv(2048)

			F, address = UDPSocket.recvfrom(bufferSize)
			
			try:
				while(F):
					UDPfile.write(F)
					UDPSocket.settimeout(2)
					F, address = UDPSocket.recvfrom(bufferSize)
			
			except socket.timeout:
				UDPfile.close()
				UDPSocket.close()
				print "File Downloaded"
				subprocess.call(['chmod', permissions, args[2]])
			
			if newHash == self.hashVal(self.UDPfile):
				self.UDPOngoing = False

	def TCPDownload(self, args):
		length = self.Socket.recv(4)
		length, = struct.unpack('I', length)
		fileInfo = self.Socket.recv(length).decode()
		print fileInfo
		temp=fileInfo.split()
		permissions = self.Socket.recv(2048)
		if temp[1] != "not":
			with open('' + args[2], 'wb') as dFile:
				while True:
					flag = 0
					data = self.Socket.recv(2048)
					if not data:
						break
					dFile.write(data)
				dFile.close()
			subprocess.call(['chmod', permissions, args[2]])

	def run(self):
		while True:
			if self.UDPOngoing:
				command = "download UDP " + self.UDPfile
			else:
				sys.stdout.write("Enter Command :")
				sys.stdout.flush
				command = raw_input()
				logFile = open("logfile" + str(self.port) + "txt", "a+")
				logFile.write(command + "\n")
				logFile.close()
			
			host = ""
			self.Socket = socket.socket()
			self.Socket.connect((host, self.port))
			args = command.split()
			
			if args[0] == "exit":
				thread1.exit()
				s.close()
				break
			
			self.Socket.send(command)
			
			if args[0] == "index":
				self.indexing(args)
			
			elif args[0] == "hash":
				self.hashup(args)
			
			elif args[0] == "download":
				if args[1] == "TCP":
					self.TCPDownload(args)
				elif args[1] == "UDP":
					self.UDPDownload(args)
				else:
					print args[0] + ": Command not found"

			else:
				print args[0] + ": Command not found"

			self.Socket.close()
		return
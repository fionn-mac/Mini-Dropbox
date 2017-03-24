import socket
import subprocess
import os
import os.path
import time
import threading
import sys
import hashlib
from sender import *
from receiver import *
from autoSender import *
from autoReceiver import *

sys.stdout.write("Manual(1)/Automated(2): ")
sys.stdout.flush
typeOfTransfer = raw_input()
n = 0

if typeOfTransfer == '1':
	thread1 = receiver(65533-n)
	thread2 = sender(65532-n)

	thread1.start()
	thread2.start()
	thread1.join()
	thread2.join()

elif typeOfTransfer == '2':
	thread1 = autoReceiver(65535-n)
	thread2 = autoSender(65534-n)

	thread1.start()
	thread2.start()
	thread1.join()
	thread2.join()

else:
	print "Closing, Wrong Inputs"
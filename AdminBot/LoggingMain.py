from twisted.python import log
import time

class LoggingMain:
	def __init__(self, file):
		self.file = file

	def log(self, msg):
		timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
		self.file.write('[%s]: %s\n' % (timestamp, msg))
		self.file.flush()

	def close(self):
		self.file.close()

import os, sys, socket, threading, traceback, time, smtplib, ssl, psutil, ctypes, configparser, shutil
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
if os.name == 'nt':
	import win32api, win32con
	pass
if getattr(sys, 'frozen', False):
	exe_path = os.path.dirname(sys.executable)
elif __file__:
	exe_path = os.path.dirname(os.path.abspath(__file__))
	pass
class socket_logger:
	def __init__(self, tmp, proc):#
		self.appLog = Log("Logger")
		self.proc = proc
		self.log = []
		self.tmpdir = tmp
		self.file = "debug.log"
		self.endstate = False
		self.quit = False
		self.error_state = False
		self.config = {}
	def read_config(self):
		try:
			config = configparser.ConfigParser()
			config.read(exe_path+'\\logger.ini')
			details = {}
			for key, value in config['EMAIL'].items():
				print(key, value)
				details[key] = value
			return details
		except Exception as err:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			self.appLog.error("read_config failed\n%s, %s, %s, %s" %(err, exc_type, exc_obj, traceback.print_tb(exc_tb)))
	def starter(self):
		try:
			self.config = self.read_config()
			t=threading.Thread(target=self.app_run)
			t.start()
			time.sleep(1)
			serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			serversocket.settimeout(5)
			serversocket.bind((socket.gethostname(), 6085))
			serversocket.listen(1)
			while not self.quit:
				try:
					clientsocket, address = serversocket.accept()
					serversocket.setblocking(1)
					break
				except:
					pass
			while not self.quit:
				data = None
				while not self.quit:
					try:
						data = clientsocket.recv(65565)
						break
					except:
						pass
				if data == b'':
					try:
						clientsocket.send(b"t", timeout=1)
					except:
						while not self.quit:
							try:
								clientsocket, address = serversocket.accept()
								serversocket.setblocking(1)
								break
							except:
								pass
				elif data == b'exit':
					self.endstate = True
					self.quit = True
				else:
					try:
						data = data.decode('utf-8')
					except:
						pass
					if data[0:3] == "Log":
						self.log_input(data)
					elif data[0:5] == "Error":
						self.error_state = True
						self.log_input(data)
			if self.endstate == False:
				self.log_input("Program exited without sending quit.")
				estate = ctypes.windll.user32.MessageBoxW(None, 'The Application closed unexpectedly.\nWould you like to send a log?', 'App Error',  1)
				if estate == 1:
					with open(self.tmpdir+"\\"+self.file, "w+") as f:
						f.write("\r\n".join(self.log))
					time.sleep(1)
					self.send_mail(self.tmpdir+"\\"+self.file)
					os.remove(self.tmpdir+self.file)
					if os.path.isdir(self.tmpdir):
						shutil.rmtree(self.tmpdir)
			elif self.error_state == True:
				self.log_input("Program exited but errors detected")
				try:
					clientsocket.close()
				except:
					pass
				estate = ctypes.windll.user32.MessageBoxW(None, 'Some Errors were detected.\nWould you like to send a log?', 'App Error',  1)
				if estate == 1:
					with open(self.tmpdir+"\\"+self.file, "w+") as f:
						f.write("\r\n".join(self.log))
					time.sleep(1)
					self.send_mail(self.tmpdir+"\\"+self.file)
					os.remove(self.tmpdir+self.file)
					if os.path.isdir(self.tmpdir):
						shutil.rmtree(self.tmpdir)
			else:
				try:
					clientsocket.close()
				except:
					pass
		except Exception as err:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			self.appLog.error("starter failed\n%s, %s, %s, %s" %(err, exc_type, exc_obj, traceback.print_tb(exc_tb)))
	def app_run(self):
		try:
			while not self.quit:
				try:
					[p.info for p in psutil.process_iter(attrs=['pid', 'name']) if self.proc in p.info['name']][0]
				except:
					self.quit = True
					break
				time.sleep(1)
		except Exception as err:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			self.appLog.error("app_run failed\n%s, %s, %s, %s" %(err, exc_type, exc_obj, traceback.print_tb(exc_tb)))
	def log_input(self, text):
		try:
			self.log.append(text)
			with open(exe_path+"\\debug.log", "a+") as f:
				f.write(text+"\r\n")
		except Exception as err:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			self.appLog.error("log_input failed\n%s, %s, %s, %s" %(err, exc_type, exc_obj, traceback.print_tb(exc_tb)))
	def send_mail(self, user, password, to file, server="smtp.live.com", server_port=587, tls=True, ssl=True, debug=False):
		try:
			msg = MIMEMultipart()
			msg['From'] = user
			msg['To'] = to
			msg['Subject'] = "Debug Log"
			msg.attach(MIMEText("System Debug Log"))
			with open(file, "rb") as fil:
				part = MIMEApplication(fil.read(), Name=os.path.basename(file))
			part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file)
			msg.attach(part)
			if ssl:
				smtp = smtplib.SMTP_SSL(server, server_port)
			else:
				smtp = smtplib.SMTP(server, server_port)
			if tls:
				smtp.ehlo()
				smtp.starttls()
				smtp.ehlo()
			smtp.login(user, password)
			if debug:
				smtp.set_debuglevel(True)
			smtp.sendmail(msg['From'], msg['To'], msg.as_string())
			smtp.quit()
		except Exception as err:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			self.appLog.error("send_mail failed\n%s, %s, %s, %s" %(err, exc_type, exc_obj, traceback.print_tb(exc_tb)))

		
class Log: #class to write to log file with time stamps
	def __init__(self, appname):
		if getattr(sys, 'frozen', False): #windows path fix
			self.exe = os.path.dirname(sys.executable)
		elif __file__:
			self.exe = self.os.path.dirname(__file__)
		if not os.path.exists(os.path.dirname(str(os.environ['USERPROFILE'])+"\\Documents\\%s\\" %appname)):
			os.makedirs(str(os.environ['USERPROFILE'])+"\\Documents\\%s\\" %appname)
		self.fname = str(os.environ['USERPROFILE'])+"\\Documents\\%s\\debug.log" %appname
		self.logfile = None
	def error(self, error):
		exc_type, exc_obj, exc_tb = sys.exc_info()
		trace_stack = traceback.extract_tb(exc_tb)[-1]
		trace_format = "Error in file "+str(trace_stack[0])+"\r		on line "+str(trace_stack[1])+", from module '"+str(trace_stack[2])+"'\r		"+str(trace_stack[3])
		try:
			self.logfile = open(self.fname, "a+")
		except:
			self.logfile = open(self.fname, "w+")
		strtime = str(time.strftime("%d-%m-%Y,(%z),%H:%M:%S"))
		self.logfile.write("error: %s, %s, %s\r" %(strtime, error, trace_format))
		self.logfile.close()
		self.logfile = None
	def log(self, log):
		try:
			self.logfile = open(self.fname, "a+")
		except:
			self.logfile = open(self.fname, "w+")
		strtime = str(time.strftime("%d-%m-%Y,(%z),%H:%M:%S"))
		self.logfile.write("log: %s, %s\r" %(strtime, log))
		self.logfile.close()
		self.logfile = None
if __name__ == "__main__":
	try:
		if len(sys.argv) == 3:
			logger = socket_logger(sys.argv[1], sys.argv[2])
			logger.starter()
		else:
			ctypes.windll.user32.MessageBoxW(None, 'The Log failed to initilise.\nFailed to create with system arguments: 1001.\nPlease Contact your Administrator', 'Logger Error',  0)
	except:
		raise
import sys, socket, select
from utils import *

class Client:

	def __init__(self, name, address, port):
		self.name = name
		self.address = address
		self.port = int(port)
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket_list = []

		try:
			self.socket.connect((address, self.port))
		except:
			print(CLIENT_CANNOT_CONNECT.format(address, port))
			sys.exit()

		if len(name) != MESSAGE_LENGTH:
			name = name.ljust(MESSAGE_LENGTH)
		self.socket.sendall(name)

	def run(self):
		
		sys.stdout.write(CLIENT_MESSAGE_PREFIX)
		sys.stdout.flush()
		
		while True:
			self.socket_list = [sys.stdin, self.socket]
			ready_to_read, ready_to_write, in_error = select.select(self.socket_list, [], [])
			

			for socket in ready_to_read:
				
				if socket == sys.stdin:
					
					message = raw_input()

					self.socket.sendall(message.ljust(MESSAGE_LENGTH))
					sys.stdout.write(CLIENT_MESSAGE_PREFIX)
					sys.stdout.flush()
					
				else:
					message = socket.recv(MESSAGE_LENGTH)
					
					# server dies
					if not message:
						sys.stdout.write(CLIENT_WIPE_ME)
						sys.stdout.flush()
						print('\r' + CLIENT_SERVER_DISCONNECTED.format(self.address, self.port))
						sys.exit()
					while len(message) != MESSAGE_LENGTH:
						tmp = socket.recv(MESSAGE_LENGTH)
						message += tmp

					message = message.rstrip()
					
					if len(message) != 0:
						sys.stdout.write(CLIENT_WIPE_ME)
						sys.stdout.write('\r' + message + '\n')
						sys.stdout.write(CLIENT_MESSAGE_PREFIX)
						sys.stdout.flush()

				
		
		self.socket.close()


args = sys.argv

if len(args) != 4:
	print("Please input 3 arguments: your name, address, port")
	sys.exit()
client_socket = Client(args[1], args[2], args[3])
client_socket.run()



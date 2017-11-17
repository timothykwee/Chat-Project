import sys, socket, select
from utils import *
from collections import defaultdict

ADDRESS = ''
CLIENTS_LIST = []
CLIENTS_NAME = {}
CHANNEL_LISTS = defaultdict(list)
CLIENTS_CHANNEL = {}
SOCKET_MSGS = defaultdict(str)

args = sys.argv

class Server:

	def __init__(self, port):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind(('', int(port)))
		self.socket.listen(5)
		CLIENTS_LIST.append(self.socket)

	def run(self):
		while True:
			ready_to_read, ready_to_write, in_error = select.select(CLIENTS_LIST, [], [], 0)

			for socket in ready_to_read:
				# A new connection established
				if socket == self.socket:
					new_socket, addr = self.socket.accept()
					CLIENTS_LIST.append(new_socket)
					name = new_socket.recv(MESSAGE_LENGTH)
					while len(name) != MESSAGE_LENGTH:
						tmp = new_socket.recv(MESSAGE_LENGTH)
						name += tmp
					name = name.rstrip()
					CLIENTS_NAME[new_socket] = name
				# A message from a client, not a new connection
				else:
					message = socket.recv(MESSAGE_LENGTH)

					# remove socket that's broken
					if not message:
						name = CLIENTS_NAME[socket]
						CLIENTS_LIST.remove(socket)
						CLIENTS_NAME.pop(socket)

						if socket in CLIENTS_CHANNEL:
							self.broadcast(socket, SERVER_CLIENT_LEFT_CHANNEL.format(name))
							channel = CLIENTS_CHANNEL[socket]
							CLIENTS_CHANNEL.pop(socket)
							CHANNEL_LISTS[channel].remove(socket)

						continue

					# while len(message) != MESSAGE_LENGTH:
					# 	tmp = socket.recv(MESSAGE_LENGTH)
					# 	message += tmp
					# message = message.rstrip()
				 
					SOCKET_MSGS[socket] += message
					
					if len(SOCKET_MSGS[socket]) < MESSAGE_LENGTH:
						continue
					
					temp = SOCKET_MSGS[socket]
					message = temp[0:MESSAGE_LENGTH]
					SOCKET_MSGS[socket] = temp[MESSAGE_LENGTH:]
					message = message.rstrip()

					# A control message
					if len(message) != 0 and message[0] == "/":
						ctrl_msg = message.split()
				
						if 'join' in ctrl_msg[0]:
							if len(ctrl_msg) != 2:
								
								socket.sendall(SERVER_JOIN_REQUIRES_ARGUMENT.ljust(MESSAGE_LENGTH))
								continue
							if ctrl_msg[1] not in CHANNEL_LISTS:
								socket.sendall(SERVER_NO_CHANNEL_EXISTS.format(ctrl_msg[1], ctrl_msg[1]).ljust(MESSAGE_LENGTH))
								continue

							CHANNEL_LISTS[ctrl_msg[1]].append(socket)

							if socket in CLIENTS_CHANNEL:
								old_channel = CLIENTS_CHANNEL[socket]
								CHANNEL_LISTS[old_channel].remove(socket)
								self.broadcast(socket, SERVER_CLIENT_LEFT_CHANNEL.format(CLIENTS_NAME[socket]))

							CLIENTS_CHANNEL[socket] = ctrl_msg[1]
							
							self.broadcast(socket, SERVER_CLIENT_JOINED_CHANNEL.format(CLIENTS_NAME[socket]))
						elif 'create' in ctrl_msg[0]:
							if len(ctrl_msg) != 2:
								socket.sendall(SERVER_CREATE_REQUIRES_ARGUMENT.ljust(MESSAGE_LENGTH))
								continue
							if ctrl_msg[1] in CHANNEL_LISTS:
								socket.sendall(SERVER_CHANNEL_EXISTS.format(ctrl_msg[1]).ljust(MESSAGE_LENGTH))
								continue
							if socket in CLIENTS_CHANNEL:
								old_channel = CLIENTS_CHANNEL[socket]
								CHANNEL_LISTS[old_channel].remove(socket)
								self.broadcast(socket, SERVER_CLIENT_LEFT_CHANNEL.format(CLIENTS_NAME[socket]))

							CHANNEL_LISTS[ctrl_msg[1]].append(socket)
							CLIENTS_CHANNEL[socket] = ctrl_msg[1]
						elif 'list' in ctrl_msg[0]:
							if len(ctrl_msg) != 1:
								socket.sendall("/list should contain no arguments".ljust(MESSAGE_LENGTH))
								continue
							allchannels = ""
							for channel in CHANNEL_LISTS:
								allchannels += channel + "\n"
							
							if (len(allchannels) != 0):
								socket.sendall(allchannels.ljust(MESSAGE_LENGTH))
							
						else:
							socket.sendall(SERVER_INVALID_CONTROL_MESSAGE.format(ctrl_msg[0]).ljust(MESSAGE_LENGTH))
					# Normal messages for chatting
					else:
						if socket not in CLIENTS_CHANNEL:
							socket.sendall(SERVER_CLIENT_NOT_IN_CHANNEL.ljust(MESSAGE_LENGTH))
							continue
						return_message = '[' + CLIENTS_NAME[socket] + '] ' + message
						self.broadcast(socket, return_message)
		
		self.socket.close()

	def broadcast(self, current_socket, message):
		curr_channel = CLIENTS_CHANNEL[current_socket]
		message = message.ljust(MESSAGE_LENGTH)
		for socket in CHANNEL_LISTS[curr_channel]:
			if socket != current_socket:
				try:
					socket.sendall(message)
				except:
					# broken socket connection
					socket.close()
					# broken socket remove it
					CHANNEL_LISTS[curr_channel].remove(socket)
					CLIENTS_CHANNEL.remove(socket)

if len(args) != 2:
	print("Please input the port number: ")
	sys.exit()
server_socket = Server(args[1])
server_socket.run()


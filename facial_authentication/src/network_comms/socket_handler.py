import asyncio, random
import websockets
import json
import time
import threading
import requests
import datetime
import os
import socket

import src.logger.custom_logger as custom_logger

LOGGER = custom_logger.get_logger()


class SocketHandler(threading.Thread):
	HOST = 'localhost'
	PORT = 9998

	def __init__(self):
		LOGGER.info("SockerHandler init...")
		super().__init__()
		self.websockets_list = []

		self.async_broadcast_msg_q = None
		self.async_event_loop = None
		self.connected_clients = set()
		self.client_handler_func = self.client_handler_3

		LOGGER.info("SocketHandler complete.")

	async def broadcast_msg(self, user=80200168, pin=123456):
		LOGGER.debug(f'\n[Total client: {len(self.websockets_list)}] Invoking _broadcast_msg()...')
		response_dict = {
			"status": "OK",
			"values": {
				"user": user,
				"pin": pin
			}
		}

		# Iterate through a copy of existing websocket list
		for websocket in self.websockets_list[:]:
			# Try to send message to connected client
			try:
				LOGGER.debug(f'[{websocket.id}] Broadcasting to client---> user: {user}, pin: {pin}')
				await websocket.send(json.dumps(response_dict))
			# If client is disconnected, remove them from list
			except websockets.exceptions.ConnectionClosed:
				LOGGER.debug(f'[{websocket.id}] websockets.exceptions.ConnectionClosed: Removing disconnected client.')
				self.websockets_list.remove(websocket)

	def broadcast_to_clients(self, employee_id, attendance):
		async def _broadcast_to_clients():
			# If there are clients connected on browser
			if len(self.connected_clients) != 0:
				await self.async_broadcast_msg_q.put(
					{
						"type": "result",
						"user": employee_id,
						"pin": "04AB1A2A313180",
						"attendance": attendance
					}
				)

		# Start the coroutine function on THIS thread
		# 	BUT using the main event loop of the socket_handler's thread
		asyncio.run_coroutine_threadsafe(_broadcast_to_clients(), self.async_event_loop)

	async def client_handler_1(self, websocket, path, extra_argument):
		LOGGER.debug(
			f'\n[{websocket.id}] Client connected from {websocket.origin}, IP: {websocket.remote_address[0]}, extra_argument: {extra_argument}')
		self.websockets_list.append(websocket)

		await asyncio.sleep(1)

		# Different ways to kickoff async method invocation
		await self.broadcast_msg(80200168, 123456)

	# https://stackoverflow.com/a/61155002/11537143
	# asyncio.get_event_loop().create_task(self.broadcast_msg(80200168, 123456))

	# https://docs.python.org/3/library/asyncio-task.html#coroutines
	# asyncio.create_task(self.broadcast_msg(80200168, 123456))

	async def client_handler_2(self, websocket, path, extra_argument):
		LOGGER.debug(
			f'\n[{websocket.id}] Client connected from {websocket.origin}, IP: {websocket.remote_address[0]}, extra_argument: {extra_argument}')
		self.websockets_list.append(websocket)

		await asyncio.sleep(1)

		# Old implementation
		response_dict = {
			"status": "OK",
			"values": {
				"user": 80200168,
				"pin": 123456
			}
		}
		await websocket.send(json.dumps(response_dict))

	async def producer(self):
		return await self.async_broadcast_msg_q.get()

	async def poll_and_broadcast_msg(self):
		# Outer loop to perform continuous polling for new msg
		while True:
			# try:
			message = await self.producer()
			user = message.get("user")
			pin = message.get("pin")

			LOGGER.info(f'Broadcasting to {len(self.connected_clients)} client(s)---> user: {user}, pin: {pin}')

			# Inner loop to ensure msg is broad-casted to all connect clients
			for client in self.connected_clients.copy():
				LOGGER.info(f'Sending msg to [{client.id}] ')
				try:
					await client.send(json.dumps(message))
					LOGGER.info(f'Message sent.')
				# If client is disconnected, remove them from list
				except websockets.exceptions.ConnectionClosed:
					LOGGER.info(f'[{client.id}] websockets.exceptions.ConnectionClosed: Removing disconnected client.')
					self.connected_clients.remove(client)

	def init_client_heartbeat_checker(self):
		def _check_client_heartbeat(delay=59):
			time.sleep(delay)
			LOGGER.debug(f'Checking client heartbeat...')
			if len(self.connected_clients) >= 1:
				LOGGER.info("Connected")
				#file_directory = "X:/Sharedfolders/Personnel Matters/Miscellaneous/ENVIS/ETCStations/Plant2R" 
				#file_path = os.path.join(file_directory, "Status.txt")
				send_to_aws = False
				if send_to_aws:
					host_name = socket.gethostname()
					ip = socket.gethostbyname(socket.gethostname())
					ping_date = str(datetime.datetime.now().date())
					timestamp = str(datetime.datetime.now().time())
					stn = "etc_stn0"
					entry_name = stn + "_" + ping_date + "_" + timestamp
					aws_url = 'https://yi7tqdi8fe.execute-api.ap-southeast-1.amazonaws.com/items'
					aws_data = {"id":entry_name,"hostname":host_name,"ip":ip,"ping_date":ping_date,"stn":stn, "timestamp":timestamp}
					#aws_data = {"id":"12","hostname":'N1-H2PWMN3-01',"ip":'10.32.80.59',"ping_date":"2024-02-26 17:45:0000","stn":"etc_stn0"}
					print(aws_data)
					#AWS Put request
					print("Sending second post request")
					headers = {'User-Agent':'PostmanRuntime/7.36.3','Accept':'*/*','Accept-Encoding':'gzip, deflate, br','Content-Type':'application/json'}
					response = requests.post(aws_url, json=aws_data,headers=headers,verify=False)
					print(response.status_code)

				# try:
				# 	print("Sending first get request")
				# 	result = requests.get("http://n1-1022-011232.stengggrp.local/microapi/post/N1-1022-011168")
				# 	LOGGER.info(f"{result=}")
                    
				# except Exception as e: 
				# 	LOGGER.error(e)
				'''
				if time.time() % 15 == 0:
					time.sleep(2)
					LOGGER.info(f"Hello world!")
					try:
						result = requests.get("http://titan-rpt.staero.sg:5000/microapi/post/N1-1022-011168")
						LOGGER.info(f"{result=}")
					except Exception as e: 
						LOGGER.error(e)
					#with open(file_path, "a") as file:
						#file.write(str(datetime.datetime.now()) + "\n")
				'''
			asyncio.run_coroutine_threadsafe(_check_heartbeat(), self.async_event_loop)

		async def _check_heartbeat():
			for client in self.connected_clients.copy():
				LOGGER.debug(f'Sending PING to [{client.id}] ')
				try:
					await client.send(json.dumps({
						"type": "ping"
					}))
				# If client is disconnected, remove them from list
				except websockets.exceptions.ConnectionClosed:
					LOGGER.debug(f'[{client.id}] websockets.exceptions.ConnectionClosed: Removing disconnected client.')
					self.connected_clients.remove(client)
			LOGGER.info(f'Active clients connection: {len(self.connected_clients)}')

		_check_client_heartbeat(0)
		while True:
			_check_client_heartbeat()

	def spawn_client_heartbeat_checker_thread(self):
		LOGGER.debug(f'Starting client heartbeat checker')
		threading.Thread(target=lambda: self.init_client_heartbeat_checker(), daemon=True).start()

	async def client_handler_3(self, websocket, path, extra_argument):
		LOGGER.info(
			f'Client[{websocket.id}] connected from {websocket.origin}, IP: {websocket.remote_address[0]}, extra_argument: {extra_argument}')
		self.connected_clients.add(websocket)
		LOGGER.info(f'Current client connection in memory: {len(self.connected_clients)}')

		await self.poll_and_broadcast_msg()

	async def start_server(self):
		LOGGER.info('Web socket server started')
		# asyncio.create_task(SocketHandler.consumer())
		self.async_broadcast_msg_q = asyncio.Queue()
		self.async_event_loop = asyncio.get_event_loop()
		LOGGER.debug(f'async_event_loop active settings: {self.async_event_loop}')

		self.spawn_client_heartbeat_checker_thread()

		LOGGER.info(f'Web socket server ready to serve')

		async with websockets.serve(
				lambda websocket, path: self.client_handler_func(websocket, path, "hej"),
				SocketHandler.HOST,
				SocketHandler.PORT
		):
			await asyncio.Future()  # run forever

	def run(self):
		asyncio.run(self.start_server(), debug=True)


def mimic_facial_recognition_process(socket_handler):
	def _gen_rand_employee_id():
		rand_num = random.randint(100, 999)
		emp_id = (80200000 + rand_num)
		return emp_id

	# Mimic facial recognition process that will take N second delay to finish
	async def _mimic_facial_recognition_process():
		while True:
			# https://websockets.readthedocs.io/en/stable/howto/faq.html
			await asyncio.sleep(5)
			LOGGER.debug('Trying to put message...')
			if len(socket_handler.connected_clients) != 0:
				LOGGER.debug('Putting message...')
				await socket_handler.async_broadcast_msg_q.put(
					{
						"status": "OK",
						"values": {
							"user": _gen_rand_employee_id(),  # 80200121
							"pin": "04AB1A2A313180"
						}
					}
				)

	# Wait 5 seconds for SocketHandler() to fully setup before mimic process begins.
	# NOTE:
	# 	INSIDE COROUTINE = asyncio.sleep()
	# 	OUTSIDE COROUTINE = time.sleep()
	time.sleep(5)

	# Start the coroutine function on THIS thread
	# 	BUT using the main event loop of the socket_handler's thread
	asyncio.run_coroutine_threadsafe(_mimic_facial_recognition_process(), socket_handler.async_event_loop)


def main():
	socket_handler = SocketHandler()
	socket_handler.start()
	threading.Thread(target=lambda: mimic_facial_recognition_process(socket_handler)).start()


if __name__ == '__main__':
	main()

import json
import asyncio

async def getINDEX(self):
    writer = self.lb_writer
    writer.write("INDEX".encode())
    await writer.drain()
    data = await self.lb_reader.read(1024)
    message = data.decode()
    if message.startswith("INDEX CODE 2"):
        self.server_index = int(message.split(";")[-1])
        print("Server INDEX:", self.server_index)
    else:
        print("Failed to get server ID from load balancer, error:", message)

async def getBORDERS(self):
    writer = self.lb_writer
    writer.write("BORDERS".encode())
    await writer.drain()
    data = await self.lb_reader.read(1024)
    message = data.decode()
    if message.startswith("BORDERS CODE 2"):
        data = message.split()[-1]
        self.server_borders[0] = int(float(data.split(";")[0]))
        self.server_borders[1] = int(float(data.split(";")[1]))
        print("Server BORDERS:", self.server_borders)
    else:
        print("Failed to get server borders from load balancer, error:", message)

async def AddToLB(self, client_id):
    async with self.players_data_lock:
        info = self.players_data[client_id].copy()
    info['server'] = self.server_id
    async with self.lb_lock:
        self.players_to_lb[client_id] = info

async def CheckForLB(self, client_id, x, y):
    if self.server_index == 1:
        if x > self.server_borders[0] or y > self.server_borders[1]:
            await self.AddToLB(client_id)
            return
    elif self.server_index == 2:
        if x < self.server_borders[0] or y < self.server_borders[1]:
            await self.AddToLB(client_id)
            return
    elif self.server_index == 3:
        if x < self.server_borders[0] or y < self.server_borders[1]:
            await self.AddToLB(client_id)
            return
    elif self.server_index == 4:
        if x > self.server_borders[0] or y < self.server_borders[1]:
            await self.AddToLB(client_id)
            return

async def SendInfoLB(self):
    writer = self.lb_writer
    async with self.lb_lock:
        data = json.dumps(self.players_to_lb)
    writer.write(f"INFO {data}".encode())
    await writer.drain()

    data = await self.lb_reader.read(1024)
    message = data.decode()
    if message != "ACK":
        print("Failed to send data to load balancer, error:", message)

async def getRIGHT(self):
    writer = self.lb_writer
    writer.write("RIGHT".encode())
    await writer.drain()
    data = await self.lb_reader.read(1024)
    data = json.loads(data.decode())
    players_to_this = []

    async with self.moving_lock:
        for client_id, server in data.items():
            if server is True:
                players_to_this.append(int(client_id))
            else:
                self.moving_servers[int(client_id)] = server

    if players_to_this:
        asyncio.create_task(self.WelcomePlayers(players_to_this, self.server_socket))

async def getSEND(self):
    writer = self.lb_writer
    async with self.other_server_lock:
        self.different_server_players = {}
        writer.write("SEND".encode())
        await writer.drain()
        data = await self.lb_reader.read(1024)
        self.different_server_players = json.loads(data.decode())

async def SendLogin(self):
    writer = self.lb_writer
    async with self.waiting_login_lock:
        if not self.waiting_login:
            return
        str_login = f"LOGIN {json.dumps(self.waiting_login)}"
    print("Sending login data to load balancer:", str_login)
    writer.write(str_login.encode())
    await writer.drain()

    data = await self.lb_reader.read(1024)
    message = data.decode()
    async with self.waiting_login_lock:
        self.waiting_login = {}
    data = json.loads(message)
    await self.SortLogin(data)

async def SortLogin(self, data):
    for client_id, data in data.items():
        client_id = int(client_id)
        prot = data[0]
        if prot.startswith("SUCCESS CODE LOGIN"):
            print(f"login for {client_id} successful!")
            async with self.secret_lock:
                self.secret_players_data[client_id] = data[1]
            async with self.clients_lock:
                data_send = data[1]
                x, y = await self.create_new_pos()
                data_send['x'] = x
                data_send['y'] = y
                writer = self.connected_clients[client_id][2]
                writer.write(f"SUCCESS CODE LOGIN {data_send}".encode())
                await writer.drain()
            async with self.players_data_lock:
                self.players_data[client_id]['x'] = x
                self.players_data[client_id]['y'] = y
        elif prot.startswith("FAILED CODE LOGIN"):
            async with self.clients_lock:
                writer = self.connected_clients[client_id][2]
                writer.write(prot.encode())
                await writer.drain()

async def SendRegister(self):
    writer = self.lb_writer
    async with self.waiting_register_lock:
        if not self.waiting_register:
            return
        print(self.waiting_register)
        str_register = f"REGISTER {json.dumps(self.waiting_register)}"
    writer.write(str_register.encode())
    await writer.drain()

    data = await self.lb_reader.read(1024)
    message = data.decode()
    async with self.waiting_register_lock:
        self.waiting_register = {}
    data = json.loads(message)
    await self.SortRegister(data)

async def SortRegister(self, data):
    for client_id, data in data.items():
        client_id = int(client_id)
        prot = data[0]
        if prot.startswith("SUCCESS CODE REGISTER"):
            print(f"register for {client_id} successful!")
            async with self.secret_lock:
                self.secret_players_data[client_id] = data[1]
            async with self.clients_lock:
                data_send = data[1]
                x, y = await self.create_new_pos()
                data_send['x'] = x
                data_send['y'] = y
                writer = self.connected_clients[client_id][2]
                writer.write(f"SUCCESS CODE REGISTER {data_send}".encode())
                await writer.drain()
            async with self.players_data_lock:
                self.players_data[client_id]['x'] = x
                self.players_data[client_id]['y'] = y
        elif prot.startswith("FAILED CODE REGISTER"):
            result = prot
            if prot == "FAILED CODE REGISTER 2":
                result = "FAILED CODE REGISTER User already exists, try logging in"
            elif prot == "FAILED CODE REGISTER 3":
                result = "FAILED CODE REGISTER Username already taken, try another one"
            async with self.clients_lock:
                writer = self.connected_clients[client_id][2]
                writer.write(result.encode())
                await writer.drain()

async def SendCache(self):
    writer = self.lb_writer
    async with self.cache_lock:
        if not self.players_cached:
            return
        str_cache = f"CACHE {json.dumps(self.players_cached)}"
    print("Sending cache data to load balancer:", str_cache)
    writer.write(str_cache.encode())
    await writer.drain()

    data = await self.lb_reader.read(1024)
    message = data.decode()
    async with self.cache_lock:
        self.players_cached = {}
    if message == "ACK":
        print("Cache data sent successfully")
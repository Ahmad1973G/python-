import json
import threading
import socket

SYN = "SYNC CODE 1"
SYN_ACK = "SYNC+ACK CODE 1"
ACK = "ACK CODE 2"

LB_PORT = 5002
UDP_PORT = LB_PORT + 1
SERVER_PORT = 5000


def recvACKLB(self):
    data = self.lb_socket.recv(1024).decode()
    if data.startswith(ACK):
        print("Received ACK")
        self.server_id = int(data.split(";")[-1])
        print("Server ID:", self.server_id)
        return True
    return False

def readSYNcLB(self, data):
    str_data = data.decode()
    if str_data.startswith(SYN):
        lb_ip, lb_port = str_data.split(" ")[-1].split(",")[0].split(";")[1], int(
            str_data.split(" ")[-1].split(",")[1].split(";")[1])
        if lb_port == LB_PORT:
            try:
                self.load_balancer_address = (lb_ip, lb_port)
                self.lb_socket.connect(self.load_balancer_address)
                print("SYNC Success")
                return True
            except Exception as e:
                print(f"Error connecting to load balancer: {e}")
    return False


def sendSYNCACKLB(self):
    self.lb_socket.send(SYN_ACK.encode())


def getINDEX(self):
    self.lb_socket.send("INDEX".encode())
    data = self.lb_socket.recv(1024).decode()
    if data.startswith("INDEX CODE 2"):
        self.server_index = int(data.split(";")[-1])
        print("Server INDEX:", self.server_index)
    else:
        print("Failed to get server ID from load balancer, error:", data)


def getBORDERS(self):
    self.lb_socket.send("BORDERS".encode())
    data = self.lb_socket.recv(1024).decode()
    if data.startswith("BORDERS CODE 2"):
        data = data.split()[-1]
        self.server_borders[0] = int(float(data.split(";")[0]))
        self.server_borders[1] = int(float(data.split(";")[1]))
        print("Server BORDERS:", self.server_borders)
    else:
        print("Failed to get server ID from load balancer, error:", data)


def AddToLB(self, client_id):
    info = self.players_data[client_id]
    info['server'] = self.server_id
    with self.lb_lock:
        self.players_to_lb[client_id] = info


def CheckForLB(self, client_id, x, y):
    if self.server_index == 1:
        if x > self.server_borders[0] or y > self.server_borders[1]:
            self.AddToLB(client_id)
            return
    if self.server_index == 2:
        if x < self.server_borders[0] or y < self.server_borders[1]:
            self.AddToLB(client_id)
            return
    if self.server_index == 3:
        if x < self.server_borders[0] or y < self.server_borders[1]:
            self.AddToLB(client_id)
            return
    if self.server_index == 4:
        if x > self.server_borders[0] or y < self.server_borders[1]:
            self.AddToLB(client_id)
            return


def SendInfoLB(self):
    with self.lb_lock:
        self.lb_socket.send(("INFO " + json.dumps(self.players_to_lb)).encode())

    data = self.lb_socket.recv(1024).decode()
    if data == "ACK":
        return
    else:
        print("Failed to send data to load balancer, error:", data)
        return

def getRIGHT(self):
    self.lb_socket.send(f"RIGHT".encode())
    data = self.lb_socket.recv(1024).decode()
    data = json.loads(data)
    players_to_this = []

    with self.moving_lock:
        for client_id, server in data.items():
            if server is True:
                players_to_this.append(client_id)
                continue
            self.moving_servers[client_id] = server

    if players_to_this:
        welcome_thread = threading.Thread(target=self.WelcomePlayers, args=(players_to_this,))
        welcome_thread.start()

def getSEND(self):
    with self.other_server_lock:
        self.different_server_players = {}
        self.lb_socket.send(f"SEND".encode())
        data = self.lb_socket.recv(1024).decode()
        data = json.loads(data)
        self.different_server_players = data

def SendLogin(self):
    try:
        with self.waiting_login_lock:
            if not self.waiting_login:
                return
            str_login = f"LOGIN {json.dumps(self.waiting_login)}"
        print("Sending login data to load balancer:", str_login)
        self.lb_socket.send(str_login.encode())
        data = self.lb_socket.recv(1024).decode()
        with self.waiting_login_lock:
            self.waiting_login = {}
        data = json.loads(data)
        self.SortLogin(self, data)

    except socket.timeout:
        print("No data received from load balancer within timeout period")

    except Exception as e:
        print(f"Error receiving data from load balancer: {e}")

def SortLogin(self, data):
    for client_id, data in data.items():
        client_id = int(client_id)
        prot = data[0]
        if prot.startswith("SUCCESS CODE LOGIN"):
            print(f"login for {client_id} successful!")
            with self.secret_lock:
                self.secret_players_data[client_id] = data[1]
            with self.clients_lock:
                data_send = data[1]
                x, y = asyncio.run()
                data_send['x'] = x
                data_send['y'] = y 
                self.connected_clients[client_id][1].send(f"SUCCESS CODE LOGIN {data_send}".encode())
            with self.players_data_lock:
                self.players_data[client_id]['x'] = x
                self.players_data[client_id]['y'] = y
            continue
        if prot.startswith("FAILED CODE LOGIN"):
            with self.clients_lock:
                self.connected_clients[client_id][1].send(prot.encode())
            continue

def SendRegister(self):
    try:
        with self.waiting_register_lock:
            if not self.waiting_register:
                return
            print(self.waiting_register)
            str_register = f"REGISTER {json.dumps(self.waiting_register)}"
        self.lb_socket.send(str_register.encode())
        data = self.lb_socket.recv(1024).decode()
        with self.waiting_register_lock:
            self.waiting_register = {}
        data = json.loads(data)
        self.SortRegister(self, data)
    except socket.timeout:
        print("No data received from load balancer within timeout period")
    except Exception as e:
        print(f"Error receiving data from load balancer: {e}")

def SortRegister(self, data):
    for client_id, data in data.items():
        client_id = int(client_id)
        prot = data[0]
        if prot.startswith("SUCCESS CODE REGISTER"):
            print(f"register for {client_id} successful!")
            with self.secret_lock:
                self.secret_players_data[client_id] = data[1]

            with self.clients_lock:
                data_send = data[1]
                x, y = self.create_new_pos()
                data_send['x'] = x
                data_send['y'] = y 
                self.connected_clients[client_id][1].send(f"SUCCESS CODE REGISTER {data_send}".encode())
            with self.players_data_lock:
                self.players_data[client_id]['x'] = x
                self.players_data[client_id]['y'] = y
            continue
        if prot.startswith("FAILED CODE REGISTER"):
            result = prot
            if prot == "FAILED CODE REGISTER 2":
                result = "FAILED CODE REGISTER User already exists, try logging in"
            elif prot == "FAILED CODE REGISTER 3":
                result = "FAILED CODE REGISTER Username already taken, try another one"
            with self.clients_lock:
                self.connected_clients[client_id][1].send(result.encode())
            continue

def SendCache(self):
    try:
        with self.cache_lock:
            if not self.players_cached:
                return
            str_cache = f"CACHE {json.dumps(self.players_cached)}"
        print("Sending cache data to load balancer:", str_cache)
        self.lb_socket.send(str_cache.encode())
        data = self.lb_socket.recv(1024).decode()
        with self.cache_lock:
            self.players_cached = {}
        if data == "ACK":
            print("Cache data sent successfully")
    except socket.timeout:
        print("No data received from load balancer within timeout period")
    except Exception as e:
        print(f"Error receiving data from load balancer: {e}")

import socket
import json
import threading
import random
import time
import sub_client_prots

# Configuration
LB_PORT = 5002
UDP_PORT = LB_PORT + 1
SERVER_PORT = 5000

# Protocol Messages
SYN = "SYNC CODE 1"
SYN_ACK = "SYNC+ACK CODE 1"
ACK = "ACK CODE 2"


def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


class SubServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind((get_ip_address(), UDP_PORT))
        self.server_address = (get_ip_address(), SERVER_PORT)
        self.server_socket.bind(self.server_address)
        self.server_socket.listen()
        self.server_socket.settimeout(5)
        self.load_balancer_address = (0, LB_PORT)
        self.connected_clients = {}
        self.is_connected_to_lb = False
        self.players_data = {}
        self.udp_socket.settimeout(4)
        self.server_id = 0
        self.server_index = 0
        self.server_borders = [0, 0]
        self.updated_elements = {}
        self.players_counter = {}
        self.players_to_lb = {}
        self.different_server_players = {}
        self.moving_servers = {}
        self.waiting_login = {}
        self.waiting_register = {}
        self.secret_players_data = {}
        self.players_cached = {}
        self.chat_logs = []
        self.sequence_id = 1
        # Add locks for shared resources
        self.clients_lock = threading.Lock()
        self.players_data_lock = threading.Lock()
        self.elements_lock = threading.Lock()
        self.counter_lock = threading.Lock()
        self.lb_lock = threading.Lock()
        self.other_server_lock = threading.Lock()
        self.moving_lock = threading.Lock()
        self.waiting_login_lock = threading.Lock()
        self.waiting_register_lock = threading.Lock()
        self.secret_lock = threading.Lock()
        self.cache_lock = threading.Lock()
        self.logs_lock = threading.Lock()
        self.sequence_lock = threading.Lock()

        self.process_move = sub_client_prots.process_move
        self.process_shoot = sub_client_prots.process_shoot
        self.process_damage_taken = sub_client_prots.process_damage_taken
        self.process_power = sub_client_prots.process_power
        self.process_angle = sub_client_prots.process_angle
        self.process_request = sub_client_prots.process_request
        self.process_requestFull = sub_client_prots.process_requestFull
        self.process_login = sub_client_prots.process_login
        self.process_register = sub_client_prots.process_register
        self.process_Money = sub_client_prots.process_Money
        self.process_Ammo = sub_client_prots.process_Ammo
        self.process_Inventory = sub_client_prots.process_Inventory
        self.process_Bomb = sub_client_prots.process_boom
        self.process_chat_recv = sub_client_prots.process_chat_recv
        self.process_chat_send = sub_client_prots.process_chat_send
        self.process_chat = sub_client_prots.process_chat

        self.protocols = {
            "MOVE": self.process_move,
            "SHOOT": self.process_shoot,
            "DAMAGE": self.process_damage_taken,
            "POWER": self.process_power,
            "ANGLE": self.process_angle,
            "LOGIN": self.process_login,
            "REGISTER": self.process_register,
            "MONEY": self.process_Money,
            "AMMO": self.process_Ammo,
            "INVENTORY": self.process_Inventory,
            "BOMB": self.process_Bomb,
            "CHAT": self.process_chat,
        }

        self.receive_protocol = {
            "REQUEST": self.process_request,
            "REQUESTFULL": self.process_requestFull
        }

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

    def AskForID(self, conn):
        try:
            conn.send("ID".encode())
            data = conn.recv(1024).decode()
            if data.startswith("ID CODE 69"):
                client_id = int(data.split(";")[-1])
                print("Received ID from client:", client_id)
                return client_id
            else:
                print("Failed to receive ID from client, error:", data)
                return -1
        except Exception as e:
            print(f"Error receiving ID from client: {e}")
            return -1

    def WelcomePlayers(self, players):
        while True:
            try:
                with self.clients_lock:
                    conn, addr = self.server_socket.accept()
                    client_id = self.AskForID(conn)

                if client_id == -1:
                    conn.close()
                    continue
                if client_id not in players:
                    continue
                with self.clients_lock:
                    self.connected_clients[client_id] = (addr, conn)
                client_thread = threading.Thread(target=self.handle_client, args=(client_id,))
                client_thread.start()
                print(f"Started thread for client {client_id} from another server")
                players.remove(client_id)
                if not players:
                    break

            except socket.timeout:
                print("No connection received within timeout period, trying again")

            except Exception as e:
                print(f"Error accepting connection from client: {e}")
                try:
                    conn.close()
                except Exception as e:
                    pass

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

    def CheckIfMoving(self, client_id):
        with self.moving_lock:
            if client_id in self.moving_servers.keys():
                return True, self.moving_servers[client_id]
            else:
                return False, 0

    def CheckIfMovingFULL(self, client_id):
        with self.clients_lock:
            cond, ip = self.CheckIfMoving(client_id)
            if not cond:
                self.connected_clients[client_id][1].send("ACK".encode())
                return

            self.connected_clients[client_id][1].send(f"MOVING {ip}".encode())

    def getSEND(self):
        with self.other_server_lock:
            self.different_server_players = {}
            self.lb_socket.send(f"SEND".encode())
            data = self.lb_socket.recv(1024).decode()
            data = json.loads(data)
            self.different_server_players = data

    def lb_connect_protocol(self):
        print("Listening on UDP for load balancer on", get_ip_address())
        while not self.is_connected_to_lb:
            try:
                data, _ = self.udp_socket.recvfrom(1024)
                print("Received UDP packet: ", data.decode())
                if self.readSYNcLB(data):
                    self.sendSYNCACKLB()
                    if self.recvACKLB():
                        self.is_connected_to_lb = True
                        lb_thread = threading.Thread(target=self.handle_lb)
                        lb_thread.start()
                        break
            except socket.timeout:
                print("No UDP packet received within timeout period")
            except Exception as e:
                print(f"Error receiving UDP packet: {e}")
                self.lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def handle_lb(self):
        self.getINDEX()
        self.getBORDERS()
        while True:
            try:
                # self.SendInfoLB()
                # self.getRIGHT()
                # self.getSEND()
                self.SendRegister()
                self.SendLogin()
                self.SendCache()
            except socket.timeout:
                print("No data received from load balancer within timeout period")
            except Exception as e:
                print(f"Error receiving data from load balancer: {e}")
                self.is_connected_to_lb = False
                break

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

    def recvACKLB(self):
        data = self.lb_socket.recv(1024).decode()
        if data.startswith(ACK):
            print("Received ACK")
            self.server_id = int(data.split(";")[-1])
            print("Server ID:", self.server_id)
            return True
        return False

    def recvSYNclient_sendSYNACK(self, data, addr):
        str_data = data.decode()
        if str_data == "SYNC CODE 69":
            self.udp_socket.sendto(f"SYNC+ACK CODE 69 {self.server_address[0]};{self.server_address[1]}".encode(), addr)
            return True
        return False

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
            self.SortLogin(data)

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
                    self.connected_clients[client_id][1].send(f"SUCCESS CODE LOGIN {data[1]}".encode())
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
            self.SortRegister(data)
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
                    self.connected_clients[client_id][1].send(f"SUCCESS CODE REGISTER {data[1]}".encode())
                continue
            if prot.startswith("FAILED CODE REGISTER"):
                with self.clients_lock:
                    self.connected_clients[client_id][1].send(prot.encode())
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

    def sendID(self):
        try:
            conn, addr = self.server_socket.accept()
            print("Accepted connection from client")
            client_id = random.randint(1, 1000)
            with self.clients_lock:
                while client_id in self.connected_clients.keys():
                    client_id = random.randint(1, 1000)
                self.connected_clients[client_id] = (addr, conn)

            with self.players_data_lock:
                self.players_data[client_id] = {}

            conn.send(f"ID CODE 69 {client_id}".encode())
            print("Sent ID to client")
            return client_id
        except Exception as e:
            print(f"Error accepting connection from client: {e}")

    def client_start_protocol(self):
        print("Listening for clients")
        try:
            data, addr = self.udp_socket.recvfrom(1024)
            if self.recvSYNclient_sendSYNACK(data, addr):
                print("Received the SYNC packet successfully")
                print("Sent the SYNC+ACK packet")
                return self.sendID()
            return -1
        except socket.timeout:
            return -1
        except Exception as e:
            print(f"Error receiving UDP packet: {e}")
            return -1

    def client_connect_protocol(self):
        print("Listening for clients on", self.server_address)
        while self.is_connected_to_lb:
            client_id = self.client_start_protocol()
            if client_id == -1:
                continue
            print(f"Client connected.")
            client_thread = threading.Thread(target=self.handle_client, args=(client_id,))
            client_thread.start()
            print(f"Started thread for client {client_id}")
            print("Connected clients:", self.connected_clients.keys())
        print("Not listening to clients anymore.")

    def handle_client(self, client_id):
        with self.clients_lock:
            conn = self.connected_clients[client_id][1]
            client_address = self.connected_clients[client_id][0]

        with self.counter_lock:
            self.players_counter[client_id] = 0

        with self.elements_lock:
            self.updated_elements[client_id] = {}

        with self.players_data_lock:
            self.players_data[client_id] = {}

        print(f"Connected to client {client_id} at {client_address}")
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                message = data.decode()
                exit_cond = self.process_player_data(client_id, message)
                if exit_cond == 1:
                    break
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            print(f"Client {client_address} disconnected.")
            with self.cache_lock and self.secret_lock:
                self.players_cached[client_id] = self.secret_players_data[client_id]
                del self.secret_players_data[client_id]
            with self.clients_lock:
                if client_id in self.connected_clients:
                    del self.connected_clients[client_id]

            with self.players_data_lock:
                if client_id in self.players_data:
                    del self.players_data[client_id]

            with self.counter_lock:
                if client_id in self.players_counter:
                    del self.players_counter[client_id]

            with self.elements_lock:
                self.updated_elements[client_id] = {'dead': True}
                start_time = time.time()
                while True:
                    if time.time() - start_time > 10:
                        del self.updated_elements[client_id]
                        break
            conn.close()

    def process_player_data(self, client_id, message: str):
        try:
            messages = message.split(' ', maxsplit=1)
            protocol = messages[0]
            data = messages[-1]
            if protocol in self.protocols.keys():
                self.protocols[protocol](self, client_id, data)

            elif protocol in self.receive_protocol.keys():
                with self.elements_lock:
                    self.updated_elements[client_id] = {}
                return self.receive_protocol[protocol](self, client_id)

            else:
                print("Unknown protocol, ignoring")

            with self.counter_lock:
                self.players_counter[client_id] = 0

            return 0
        except Exception as e:
            print(f"Error processing player data for {client_id}: {e}")

    def run(self):
        lb_thread = threading.Thread(target=self.lb_connect_protocol)
        lb_thread.start()
        lb_thread.join()

        if self.is_connected_to_lb:
            self.client_connect_protocol()
        else:
            print("Load balancer not properly connected, not listening to clients.")


if __name__ == "__main__":
    server = SubServer()
    server.run()
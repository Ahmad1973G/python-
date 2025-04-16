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

        # Add locks for shared resources
        self.clients_lock = threading.Lock()
        self.players_data_lock = threading.Lock()
        self.elements_lock = threading.Lock()
        self.counter_lock = threading.Lock()
        self.lb_lock = threading.Lock()

        self.process_move = sub_client_prots.process_move
        self.process_shoot = sub_client_prots.process_shoot
        self.process_damage_taken = sub_client_prots.process_damage_taken
        self.process_power = sub_client_prots.process_power
        self.process_angle = sub_client_prots.process_angle
        self.process_request = sub_client_prots.process_request
        self.process_requestFull = sub_client_prots.process_requestFull

        self.protocols = {
            "MOVE": self.process_move,
            "SHOOT": self.process_shoot,
            "DAMAGE": self.process_damage_taken,
            "POWER": self.process_power,
            "ANGLE": self.process_angle
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
            print("Server INDEX:", self.server_id)
        else:
            print("Failed to get server ID from load balancer, error:", data)

    def getBORDERS(self):
        self.lb_socket.send("BORDERS".encode())
        data = self.lb_socket.recv(1024).decode()
        if data.startswith("BORDERS CODE 2"):
            data = data.split()[-1]
            self.server_borders[0] = int(data.split(";")[0])
            self.server_borders[1] = int(data.split(";")[1])
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

    def getRIGHT(self):
        with self.lb_lock:
            self.lb_socket.send(f"RIGHT".encode())
            data = self.lb_socket.recv(1024).decode()
            data = json.loads(data)
            pass

    def getSEND(self):
        with self.lb_lock:
            self.lb_socket.send(f"SEND".encode())
            data = self.lb_socket.recv(1024).decode()
            data = json.loads(data)
            for client_id, data in data.items():
                with self.elements_lock:
                    self.updated_elements[client_id] = data
            start_time = time.time()
            while time.time() < start_time + 3:
                pass
            with self.elements_lock:
                for client_id in data.keys():
                    if client_id in self.updated_elements.keys():
                        del self.updated_elements[client_id]

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
                self.SendInfoLB()
                data = self.lb_socket.recv(1024).decode()
                pass
            except socket.timeout:
                print("No data received from load balancer within timeout period")
            except Exception as e:
                print(f"Error receiving data from load balancer: {e}")
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
            messages = message.split(' ')
            protocol = messages[0]
            data = messages[-1]
            if protocol in self.protocols.keys():
                self.protocols[protocol](client_id, data)

            elif protocol in self.receive_protocol.keys():
                return self.receive_protocol[protocol](client_id)

            else:
                print("Unknown protocol, ignoring")

            with self.counter_lock:
                if client_id in self.players_counter.keys():
                    self.players_counter[client_id] = 0
                else:
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

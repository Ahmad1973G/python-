import socket
import json
import threading
import time
import random
from typing import Union, Tuple, Dict, Any, Optional
import database  

thread_local = threading.local()

class LoadBalancer:
    def __init__(self):
        self.IP = self.get_ip_address()
        self.PORT = 5002
        self.servers = {}  # Store connected servers (ID -> socket)
        self.servers_index = {'1': None, '2': None, '3': None, '4': None}  # Store server index (ID -> index)
        self.map_width, self.map_height = 38400, 34560
        self.max_attack = 300
        self.server_borders = (self.map_width / 2, self.map_height / 2)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.IP, self.PORT))  # Bind the socket to the address
        self.socket.listen(5)  # Listen for incoming connections
        self.socket.settimeout(5)
        print(f"Load Balancer on {self.IP}:{self.PORT}")
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.final_packet_right = {}
        self.final_packet_to_send = {}
        self.protocols = {
            'INFO': self.process_info,
            'LOGIN': self.process_login,
            'REGISTER': self.process_register,
            'CACHE': self.process_cache,
        }

        self.db_lock = threading.Lock()  # Add database lock
        self.right_lock = threading.Lock()
        self.send_lock = threading.Lock()

    def get_db(self):
        if not hasattr(thread_local, "db"):
            thread_local.db = database.database()
        return thread_local.db

    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address

    def createSYNCpacket(self):
        packet = "SYNC CODE 1, IP;" + self.IP + ",PORT;" + str(self.PORT)
        return packet.encode()

    def read_sa_send_ack(self, conn):
        data = conn.recv(1024)
        str_data = data.decode()
        if str_data == 'SYNC+ACK CODE 1':
            id = random.randint(1, 1000)
            while id in self.servers.keys():
                id = random.randint(1, 1000)
            for key, value in self.servers_index.items():
                if value is None:
                    self.servers_index[key] = id
                    break
            self.servers[id] = conn
            conn.send(f"ACK CODE 2;{id}".encode())
            print("Received the SYNC+ACK packet successfully")
            print("Sent the ACK packet")
            return True, id
        return False, id

    def MoveServer(self, packet_info, server_borders) -> Tuple[Dict, Dict]:
        right_servers = {}
        server_to_send = {}
        for id, properties in packet_info.items():
            if properties["x"] < server_borders[0] and properties["y"] < server_borders[1]:
                right_servers[id] = self.servers_index['1']
            elif properties["x"] > server_borders[0] and properties["y"] > server_borders[1]:
                right_servers[id] = self.servers_index['3']
            elif properties["x"] < server_borders[0] and properties["y"] > server_borders[1]:
                right_servers[id] = self.servers_index['4']
            else:
                right_servers[id] = self.servers_index['2']

            self.HandlePlayerServer(id, properties, server_to_send, right_servers)

        return right_servers, server_to_send

    def broadcast_packet(self, packet, port):
        self.udp_socket.sendto(packet, ('255.255.255.255', port))

    def HandlePlayerServer(self, client_id, properties, server_to_send, right_servers):
        if self.server_borders[0] - self.max_attack < properties['x'] < self.server_borders[0] + self.max_attack:
            if properties['y'] < self.server_borders[1] - self.max_attack:
                server_to_send[client_id] = [self.servers_index['1'], self.servers_index['2']]
            elif properties['y'] > self.server_borders[1] + self.max_attack:
                server_to_send[client_id] = [self.servers_index['3'], self.servers_index['4']]
            else:
                server_to_send[client_id] = [self.servers_index['1'], self.servers_index['2'], self.servers_index['3'],
                                             self.servers_index['4']]
        else:
            if properties['x'] < self.server_borders[0] - self.max_attack:
                server_to_send[client_id] = [self.servers_index['1'], self.servers_index['4']]
            else:
                server_to_send[client_id] = [self.servers_index['2'], self.servers_index['3']]

        server_to_send[client_id].remove(properties['server'])

    def start_protocol(self):
        while len(self.servers) < 5:
            self.broadcast_packet(self.createSYNCpacket(), self.PORT + 1)
            print("Sent SYNC packet again")

            try:
                conn, _ = self.socket.accept()  # Will time out after 2 seconds
                tr, id = self.read_sa_send_ack(conn)
                if tr:
                    print("Sent id to server")
                    print(f"{len(self.servers)} Servers connected")
                    server_thread = threading.Thread(target=self.handle_server, args=(id,))
                    server_thread.start()
                else:
                    conn.close()

            except socket.timeout:
                print("No connection received within timeout period")
            except Exception as e:
                print(f"Error accepting connection: {e}")
                try:
                    conn.close()
                except Exception as e:
                    pass

    def run(self):
        self.start_protocol()

    def process_info(self, data, id):
        try:
            data = json.loads(data)
            right_servers, server_to_send = self.MoveServer(data, self.server_borders)

            for client_id, server in right_servers.items():
                with self.right_lock:
                    self.final_packet_right[server][client_id] = True
                    self.final_packet_right[data[client_id]['server']][client_id
                    ] = self.servers[server].getpeername()[0]

            for client_id, servers in server_to_send.items():
                with self.send_lock:
                    for server in servers:
                        self.final_packet_to_send[server] = data[client_id]

            self.servers[id].send("ACK".encode())
        except Exception as e:
            print(f"Error processing info: {e}")
            return



    def getRIGHT(self, server_id):
        with self.right_lock:
            self.servers[server_id].send(f"RIGHT CODE 2;{self.final_packet_right[server_id]}".encode())
            self.final_packet_right[server_id] = {}

    def getSEND(self, server_id):
        with self.send_lock:
            self.servers[server_id].send(f"SEND CODE 2;{self.final_packet_to_send[server_id]}".encode())
            self.final_packet_to_send[server_id] = {}

    def process_cache(self, data, id):
        try:
            data = json.loads(data)
            for client_id, properties in data.items():
                with self.db_lock:
                    db = self.get_db()
                    db.updateplayer(properties['PlayerID'], properties['PlayerModel'], properties['PlayerLifecount'],
                                    properties['PlayerMoney'], properties['Playerammo'], properties['Playerslot1'],
                                    properties['Playerslot2'], properties['Playerslot3'], properties['Playerslot4'],
                                    properties['Playerslot5'])

            self.servers[id].send("ACK".encode())
        except json.JSONDecodeError:
            print(f"Error decoding JSON data: {data}")
            return
        except Exception as e:
            print(f"Error processing cache data: {e}")
            return


    def process_login(self, data, id):
        try:
            print(f"Login request received from server {id}")
            clients = {}
            data = json.loads(data)
            for client_id, data in data.items():
                try:
                    username = data[0]
                    password = data[1]

                    with self.db_lock:  # Protect database access
                        db = self.get_db()
                        if db.login(username, password) is True:
                            player = db.getallplayer(username)
                            clients[client_id] = ("SUCCESS CODE LOGIN", player)
                        else:
                            clients[client_id] = ("FAILED CODE LOGIN 1", None)
                except Exception as e:
                    print(f"Error processing login data for client {client_id}: {e}")
                    clients[client_id] = (f"FAILED CODE LOGIN {e}", None)

            self.servers[id].send(json.dumps(clients).encode())

        except json.JSONDecodeError:
            print(f"Error decoding JSON data: {data}")
            return
        except Exception as e:
            print(f"Error processing login data: {e}")
            return

    def process_register(self, data, id):
        try:
            clients = {}
            data = json.loads(data)
            for client_id, data in data.items():
                username = data[0]
                password = data[1]

                try:
                    with self.db_lock:  # Protect database access
                        db = self.get_db()
                        if db.login(username, password) is True:
                            clients[client_id] = ("FAILED CODE REGISTER 2", None)
                            continue
                        if db.user_exists(username):
                            clients[client_id] = ("FAILED CODE REGISTER 3", None)
                            continue
                        db.createplayer(1, username, password)
                        data = db.getallplayer(username)
                        clients[client_id] = ("SUCCESS CODE REGISTER", data)
                except Exception as e:
                    print(f"Error processing register data for client {client_id}: {e}")
                    clients[client_id] = (f"FAILED CODE REGISTER {e}", None)
            self.servers[id].send(json.dumps(clients).encode())

        except json.JSONDecodeError:
            print(f"Error decoding JSON data: {data}")
            return
        except Exception as e:
            print(f"Error processing register data: {e}")
            return

    def handle_server(self, id):
        while True:
            try:
                data = self.servers[id].recv(1024).decode()
                if not data:
                    break

                try:
                    if data.startswith("INDEX"):
                        print(f"INDEX request received from server {id}")
                        for key, value in self.servers_index.items():
                            if value == id:
                                self.servers[id].send(f"INDEX CODE 2;{key}".encode())
                                break
                        continue

                    if data.startswith("BORDERS"):
                        print(f"BORDERS request received from server {id}")
                        self.servers[id].send(f"BORDERS CODE 2 {self.server_borders[0]};{self.server_borders[1]}".encode())
                        continue

                    protocol = data.split(" ")[0]
                    data = data.split(" ", maxsplit=1)[1]
                    if protocol in self.protocols:
                        self.protocols[protocol](data, id)
                    else:
                        print(f"Unknown protocol {protocol} from server {id}")
                        continue

                except json.JSONDecodeError:
                    print(f"Error decoding JSON data from server {id}: {data}")
                    continue
                except Exception as e:
                    print(f"Error processing data from server {id}: {e}")

            except socket.timeout:
                print(f"Socket timeout for server {id}")
                continue

            except Exception as e:
                print(f"Error handling server {id}: {e}")
                print(f"Server {id} disconnected")
                break

        del self.servers[id]
        for key, value in self.servers_index.items():
            if value == id:
                self.servers_index[key] = None

if __name__ == "__main__":
    lb = LoadBalancer()
    lb.run()  # Start listening and handling connections
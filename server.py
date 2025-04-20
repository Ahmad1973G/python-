import socket
import json
import threading
import random
import time

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
        self.updated_elements = {}
        self.players_counter = {}
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

        # Add locks for shared resources
        self.clients_lock = threading.Lock()
        self.players_data_lock = threading.Lock()
        self.elements_lock = threading.Lock()
        self.counter_lock = threading.Lock()

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
                        break
            except socket.timeout:
                print("No UDP packet received within timeout period")
            except Exception as e:
                print(f"Error receiving UDP packet: {e}")
                self.lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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

    def process_move(self, client_id, message: str):
        try:
            x = message.split(';')[0]
            y = message.split(';')[1]
            with self.elements_lock:
                self.updated_elements[client_id]['x'] = x
                self.updated_elements[client_id]['y'] = y
            with self.players_data_lock:
                self.players_data[client_id]['x'] = x
                self.players_data[client_id]['y'] = y
            with self.clients_lock:
                self.connected_clients[client_id][1].send("ACK".encode())
        except Exception as e:
            print(f"Error processing move for {client_id}: {e}")

    def process_shoot(self, client_id, message: str):
        try:
            messages = message.split(';')
            start_x = messages[0]
            start_y = messages[1]
            end_x = messages[2]
            end_y = messages[3]
            weapon = messages[4]
            with self.elements_lock:
                self.updated_elements[client_id]['shoot'] = [start_x, start_y, end_x, end_y, weapon]
            with self.clients_lock:
                self.connected_clients[client_id][1].send("ACK".encode())
        except Exception as e:
            print(f"Error processing shoot for {client_id}: {e}")

    def process_damage_taken(self, client_id, message: str):
        try:
            damage = message
            with self.elements_lock:
                self.updated_elements[client_id]['health'] -= damage
            with self.players_data_lock:
                self.players_data[client_id]['health'] -= damage
            with self.clients_lock:
                self.connected_clients[client_id][1].send("ACK".encode())
        except Exception as e:
            print(f"Error processing damage taken for {client_id}: {e}")

    def process_power(self, client_id, message: str):
        try:
            power = message.split(';')
            with self.elements_lock:
                self.updated_elements[client_id]['power'] = power, self.players_data['x'], self.players_data['y']
            with self.clients_lock:
                self.connected_clients[client_id][1].send("ACK".encode())
        except Exception as e:
            print(f"Error processing power for {client_id}: {e}")

    def process_angle(self, client_id, message: str):
        try:
            angle = float(message)
            with self.elements_lock:
                self.updated_elements[client_id]['angle'] = angle
            with self.players_data_lock:
                self.players_data[client_id]['angle'] = angle
            with self.clients_lock:
                self.connected_clients[client_id][1].send("ACK".encode())
        except Exception as e:
            print(f"Error processing angle for {client_id}: {e}")

    def process_request(self, client_id):
        try:
            with self.counter_lock:
                self.players_counter[client_id] += 1
                counter = self.players_counter[client_id]

            if counter == 10000:
                with self.clients_lock:
                    self.connected_clients[client_id][1].send("WARNING".encode())
                return 0
            elif counter == 100000:
                with self.clients_lock:
                    self.connected_clients[client_id][1].send("KICK".encode())
                    self.connected_clients[client_id][1].close()
                return 1

            with self.elements_lock:
                other_players_data = {player_id: data for player_id, data in self.updated_elements.items() if
                                      data != {}}

            other_players_data_str = json.dumps(other_players_data)
            with self.clients_lock:
                self.connected_clients[client_id][1].send(other_players_data_str.encode())
        except Exception as e:
            print(f"Error processing request for {client_id}: {e}")
        finally:
            return 0

    def process_requestFull(self, client_id):
        try:
            with self.counter_lock:
                self.players_counter[client_id] += 1
                counter = self.players_counter[client_id]

            if counter == 10000:
                with self.clients_lock:
                    self.connected_clients[client_id][1].send("WARNING".encode())
                return 0
            elif counter == 100000:
                with self.clients_lock:
                    self.connected_clients[client_id][1].send("KICK".encode())
                    self.connected_clients[client_id][1].close()
                return 1

            with self.players_data_lock:
                other_players_data = {player_id: data for player_id, data in self.players_data.items() if data != {}}

            other_players_data_str = json.dumps(other_players_data)
            with self.clients_lock:
                self.connected_clients[client_id][1].send(other_players_data_str.encode())
        except Exception as e:
            print(f"Error processing request for {client_id}: {e}")
        finally:
            return 0

    def process_player_data(self, client_id, message: str):
        try:
            messages = message.split(' ')
            protocol = messages[0]
            data = messages[-1]
            if protocol in self.protocols.keys():
                self.protocols[protocol](client_id, data)

            elif protocol in self.receive_protocol.keys():
                with self.elements_lock:
                    if 'shoot' in self.updated_elements[client_id].keys():
                        pass
                    print(self.updated_elements[client_id])
                    self.updated_elements[client_id] = {}

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
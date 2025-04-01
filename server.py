import socket
import json
import threading
import random

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
            while client_id in self.connected_clients.keys():
                client_id = random.randint(1, 1000)
            self.connected_clients[client_id] = (addr, conn)
            self.players_data[client_id] = {}
            conn.send(f"ID CODE 69 {client_id}".encode())
            print("Sent ID to client")
            self.connected_clients[client_id] = (addr, conn)
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
        conn = self.connected_clients[client_id][1]
        client_address = self.connected_clients[client_id][0]
        self.players_counter[client_id] = 0
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
            del self.connected_clients[client_id]
            del self.players_data[client_id]
            conn.close()

    def process_move(self, client_id, message: str):
        try:
            x = message.split(';')[0]
            y = message.split(';')[1]
            self.updated_elements[client_id]['x'] = x
            self.updated_elements[client_id]['y'] = y
            self.players_data[client_id]['x'] = x
            self.players_data[client_id]['y'] = y
        except Exception as e:
            print(f"Error processing move for {client_id}: {e}")

    def process_shoot(self, client_id, message: str):
        try:
            start_x = message.split(';')[0]
            start_y = message.split(';')[1]
            end_x = message.split(';')[2]
            end_y = message.split(';')[3]
            self.updated_elements[client_id]['shoot'] = (start_x, start_y, end_x, end_y)
        except Exception as e:
            print(f"Error processing shoot for {client_id}: {e}")

    def process_damage_taken(self, client_id, message: str):
        try:
            damage = message
            self.updated_elements[client_id]['health'] -= damage
            self.players_data[client_id]['health'] -= damage
        except Exception as e:
            print(f"Error processing damage taken for {client_id}: {e}")

    def process_power(self, client_id, message: str):
        try:
            power = message.split(';')
            self.updated_elements[client_id]['power'] = power, self.players_data['x'], self.players_data['y']
        except Exception as e:
            print(f"Error processing power for {client_id}: {e}")

    def process_request(self, client_id):
        try:
            self.players_counter[client_id] += 1
            if self.players_counter[client_id] == 500:
                self.connected_clients[client_id][1].send("WARNING".encode())
                return 0
            elif self.players_counter[client_id] == 1000:
                self.connected_clients[client_id][1].send("KICK".encode())
                self.connected_clients[client_id][1].close()
                return 1

            other_players_data = {player_id: data for player_id, data in self.updated_elements.items() if player_id != client_id}
            other_players_data_str = json.dumps(other_players_data)
            self.connected_clients[client_id][1].send(other_players_data_str.encode())
        except Exception as e:
            print(f"Error processing request for {client_id}: {e}")
        finally:
            return 0

    def process_player_data(self, client_id, message: str):
        try:
            self.updated_elements[client_id] = {}
            if message.startswith("MOVE"):
                self.process_move(client_id, message.split(" ")[-1])
            elif message.startswith("SHOOT"):
                self.process_shoot(client_id, message.split(" ")[-1])
            elif message.startswith("DAMAGE"):
                self.process_damage_taken(client_id, message.split(" ")[-1])
            elif message.startswith("POWER"):
                self.process_power(client_id, message.split(" ")[-1])
            elif message.startswith("REQUEST"):
                return self.process_request(client_id)

            if self.updated_elements != {}:
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
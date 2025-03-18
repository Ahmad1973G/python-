import socket
import json
import threading
import time
import random
from typing import Union

class LoadBalancer:
    def __init__(self):
        self.IP = self.get_ip_address()
        self.PORT = 5002
        self.servers = {} # Store connected servers (ID -> socket)
        self.map_width, self.map_height = 38400, 34560
        self.max_attack = 300
        self.server_borders = (self.map_width / 2, self.map_height / 2)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.time = time.time()
        self.socket.bind((self.IP, self.PORT))  # Bind the socket to the address
        self.socket.listen(5)  # Listen for incoming connections
        self.socket.settimeout(5)
        print(f"Load Balancer on {self.IP}:{self.PORT}")
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.IP, self.PORT + 1))
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

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
            self.servers[id] = conn
            conn.send(f"ACK CODE 2;{id}".encode())
            print("Received the SYNC+ACK packet successfully")
            print("Sent the ACK packet")
            return True, id
        return False, id

    
    def MoveServer(self, packet_info, server_borders) -> Union[dict, dict]:
        right_servers = {}
        server_to_send = {}
        for id, properties in packet_info.items():
            if properties["x"] < server_borders[0] and properties["y"] < server_borders[1]:
                right_servers[id] = 1
            elif properties["x"] > server_borders[0] and properties["y"] > server_borders[1]:
                right_servers[id] = 3
            elif properties["x"] < server_borders[0] and properties["y"] > server_borders[1]:
                right_servers[id] = 4
            else:
                right_servers[id] = 2

            self.HandlePlayerServer(id, properties, server_to_send, right_servers)

        return right_servers, server_to_send

    def broadcast_packet(self, packet, port):
        self.udp_socket.sendto(packet, ('255.255.255.255', port))

    def HandlePlayerServer(self, id, properties, server_to_send, right_servers):
        if (self.server_borders[0] - self.max_attack < properties['x'] < self.server_borders[0] + self.max_attack):
            if (properties['y'] < self.server_borders[1] - self.max_attack):
                server_to_send[id] = [1, 2]
            elif (properties['y'] > self.server_borders[1] + self.max_attack):
                server_to_send[id] = [3, 4]
            else:
                server_to_send[id] = [1, 2, 3, 4]
        else:
            if (properties['x'] < self.server_borders[0] - self.max_attack):
                server_to_send[id] = [1, 4]
            else:
                server_to_send[id] = [2, 3]

        server_to_send[id].remove(properties['server'])

    def packet_info(data):
        """
        Extracts and decodes the packet information.
        Args:
            data: The raw packet data.
        Returns:
            dict: The decoded packet information.
        """
        str_data = data.decode()
        try:
            return json.loads(str_data.decode())
        except:
            print("Error: Could not decode packet")
            return None

    def start_protocol(self):
        while self.servers.__len__() <= 5:
            self.broadcast_packet(self.createSYNCpacket(),  self.udp_socket.getsockname()[1])
            print("Sent SYNC packet again")
            
            try:
                conn, _ = self.socket.accept()  # Will time out after 2 seconds
                tr, id = self.read_sa_send_ack(conn)
                if tr:
                    print("Sent id to server")
                    print(f"{self.servers.__len__()} Servers connected")
                    server_thread = threading.Thread(target=self.handle_server, args=(id,))
                    server_thread.start()
                else:
                    conn.close()

            except socket.timeout:
                print("No connection received within timeout period")
            except Exception as e:
                print(f"Error accepting connection: {e}")
                conn.close()

    def run(self):
        self.start_protocol()

    def handle_server(self, id):
        count = 0
        conn = self.servers[id]
        conn.settimeout(5)
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                count = 0
                packet_info = self.packet_info(data)
                if packet_info:
                    right_servers, server_to_send = self.MoveServer(packet_info, self.server_borders)
                    for id, server in server_to_send.items():
                        for s in server:
                            self.servers[s - 1].send(json.dumps({id: packet_info[id]}).encode())
                    conn.send(json.dumps(right_servers).encode())
            except socket.timeout:
                print("No data received within timeout period")
                count += 1
                if count == 50:
                    print("Server disconnected")
                    break
            
            except Exception as e:
                print(f"Error handling server: {e}")
                break

        print("Server disconnected")
        del self.servers[id]

if __name__ == "__main__":
    lb = LoadBalancer()
    lb.run() # Start listening and handling connections

import socket
import json
import threading
import time

class LoadBalancer:
    def __init__(self):
        self.IP = self.get_ip_address()
        self.PORT = 5000
        self.servers = []
        self.map_width, self.map_height = 38400, 34560
        self.max_attack = 300
        self.server_borders = (self.map_width / 2, self.map_height / 2)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.time = time.time()

    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    
    def createSYNCpacket(self):
        packet = "SYNC CODE 1"
        return packet.encode()

    def read_sa_send_ack(self, conn):
        data = conn.recv(1024)
        str_data = data.decode()
        if str_data == 'SYNC+ACK CODE 1':
            conn.send(f"ACK CODE 2 IP.{conn.getpeername()[0]} PORT.{conn.getpeername()[1]}".encode())
            print("Received the SYNC+ACK packet successfully")
            print("Sent the ACK packet")
            return True
        return False

    def read_ack(self, conn):
        data = conn.recv(1024)
        str_data = data.decode()
        if str_data == 'ACK CODE 2':
            print("Received the ACK packet successfully from IP: ", conn.getpeername()[0], " Port: ", conn.getpeername()[1])
            return True
        else:
            return False


    def MoveServer(self, packet_info, server_borders) -> dict | dict:
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
        """
        Broadcasts a packet to the network.
        
        Args:
            packet (bytes): The packet to broadcast.
            port (int): The port to broadcast the packet on.
        """
        # Create a UDP socket
        # Enable broadcasting mode
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Broadcast the packet to the broadcast address
        # The broadcast address is a special address used to send data to all possible destinations in the network.
        broadcast_address = '<broadcast>'
        self.socket.sendto(packet, (broadcast_address, port))

        # Disable broadcasting mode
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)

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


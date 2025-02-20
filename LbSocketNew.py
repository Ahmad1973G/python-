import socket
import json
import threading

class LoadBalancer:
    def __init__(self):
        self.LbIP = self.get_ip_address()
        self.LbPORT = 0
        self.servers = []
        self.map_width, self.map_height = 38400, 34560
        self.max_attack = 300
        self.server_borders = (self.map_width / 2, self.map_height / 2)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    
    def createSYNCpacket(self):
        packet = "SYNC CODE 1"
        return packet.encode()

    def read_sa_send_ack(self, data):
        str_data = data.decode()
        if (str_data == 'SYNC+ACK CODE 1'):
            self.sock.sendto("ACK CODE 2".encode(), (self.LbIP, self.LbPORT))
            print("Received the SYNC+ACK packet successfully")
            print("Sent the ACK packet")
            return True
        
        return False

    def read_ack(self, data):
        str_data = data.decode()
        if (str_data == 'ACK CODE 2'):
            print("Received the ACK packet successfully")
            return True
        else:
            return False
    def start_protocol(self):
        self.socket.bind((self.LbIP, self.LbPORT))
        self.LbPORT = self.socket.getsockname()[1]
        print(f"Server is running on IP: {self.LbIP}, Port: {self.LbPORT}")
        print("Sent the SYNC packet")
        self.broadcast_packet(self.createSYNCpacket(), 5000)
        self.socket.listen()
        count = 0
        print("Server is waiting for a response")
        while count < 5:
            data, addr = self.socket.recvfrom(1024)
            if (not self.read_sa_send_ack(data)):
                continue

            data1, addr1 = self.socket.recvfrom(1024)
            if (addr1 != addr):
                continue

            if (self.read_ack(data1)):
                count += 1
                self.servers.append(addr)
                print(f"Server added to the list, IP: {addr[0]}, Port: {addr[1]}")
            else:
                count += 1
        print("All servers are connected")
        print("Servers: ", self.servers)


    def ARP_request(self):
        data = "ARP REQUEST CODE 1"
        self.broadcast_packet(data.encode(), 5000)
        print("Sent the ARP request")
        self.socket.listen()
        count = 0
        print("Server is waiting for a response")
        while count < 5:
            data, addr = self.socket.recvfrom(1024)
            if (self.read_arp_reply(data)):
                count += 1

    def read_arp_reply(self, data):
        str_data = data.decode()
        if (str_data == 'ARP REPLY CODE 1'):
            print("Received the ARP reply")
            return True
        else:
            return False

    def MoveServer(self, packet_info, server_borders) -> (dict, dict):
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

            HandlePlayerServer(id, properties, server_to_send, right_servers)
            
        return right_servers, server_to_send
    
    def broadcast_packet(self, packet, port):
        """
        Broadcasts a packet to the network.
        
        Args:
            packet (bytes): The packet to broadcast.
            port (int): The port to broadcast the packet on.
        """
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enable broadcasting mode
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Broadcast the packet to the broadcast address
        # The broadcast address is a special address used to send data to all possible destinations in the network.
        broadcast_address = '<broadcast>'
        sock.sendto(packet, (broadcast_address, port))
        # Close the socket
        sock.close()

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


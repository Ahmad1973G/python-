import socket
import json
import threading

class LoadBalancer:
    def __init__(self):
        self.LbIP = self.get_ip_adress()
        self.LbPORT = 0
        self.servers = []
        self.map_width, self.map_height = 38400, 34560
        self.max_attack = 300
        self.server_borders = (self.map_width / 2, self.map_height / 2)

    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    
    def start_protocol(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.LbIP, self.LbPORT))
        self.LbPORT = self.sock.getsockname()[1]
        print(f"Server is running on IP: {self.LbIP}, Port: {self.LbPORT}")

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
    
    def HandlePlayerServer(self, id, properties, server_to_send, right_servers):
        if (self.server_borders[0] - self.max_attack < properties['x'] < self.server_borders[0] + self.max_attack):
            if (properties['y'] < self.server_borders[1] - self.max_attack):
                server_to_send[id] = [1, 2]
            elif (properties['y'] > self.server_borders[1] + self.max_attack):
                server_to_send[id] = [3, 4]
            else:
                server_to_send[id] = [1, 22, 3, 4]
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


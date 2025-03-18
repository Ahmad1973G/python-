import socket
import json
import threading
import random

# Configuration
LB_PORT = 5002  # Replace with the load balancer port
UDP_PORT = LB_PORT + 1  # Replace with the load balancer UDP port
SERVER_PORT = 5000  # Let the OS assign a port

# Protocol Messages
SYN = "SYNC CODE 1"
SYN_ACK = "SYNC+ACK CODE 1"
ACK = "ACK CODE 2"


class SubServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Changed to TCP
        self.lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind(('0.0.0.0', UDP_PORT))
        self.server_address = (self.get_ip_address(), SERVER_PORT)
        self.server_socket.bind(self.server_address)
        self.server_socket.listen()  # Listen for incoming connections
        self.server_socket.settimeout(5)
        self.load_balancer_address = (0, LB_PORT)
        self.connected_clients = {}  # Store connected clients' addresses (ID -> ((IP, port), socket))
        self.is_connected_to_lb = False
        self.players_data = {}  # Dictionary to store player information (ID -> data))
        self.udp_socket.settimeout(4) # Set a timeout for UDP socket
        self.id = 0
        self.ids = []

    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address

    def lb_connect_protocol(self):
        """Handles the connection protocol with the load balancer."""
        print("Listening on UDP for load balancer on", self.get_ip_address())
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
            lb_ip, lb_port = str_data.split(" ")[-1].split(",")[0].split(";")[1], int(str_data.split(" ")[-1].split(",")[1].split(";")[1])
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
            self.id = int(data.split(";")[-1])
            print("ID:", self.id)
            return True
        return False

    def recvSYNclient_sendSYNACK(self, data, addr):
        str_data = data.decode()
        if str_data == "SYNC CODE 69":
            self.udp_socket.sendto(f"SYNC+ACK CODE 69 {self.server_address[0]};{self.server_address[1]}".encode(), addr)
            return True
        return False

    def recvACKclient_sendID(self, data, addr):
        try:
            conn, addr = self.server_socket.accept()
            print("Accepted connection from client")
            id = random.randint(1, 1000)
            while id in self.ids:
                id = random.randint(1, 1000)
            self.ids.append(id)
            conn.send(f"ID CODE 69 {id}".encode())
            print("Sent ID to client")
            self.connected_clients[id] = (addr, conn)
            return id
        except Exception as e:
            print(f"Error accepting connection from client: {e}")

    def client_start_protocol(self):
        """Handles the connection protocol with clients."""
        print("Listening for clients")
        try:
            data, addr = self.udp_socket.recvfrom(1024)
            if self.recvSYNclient_sendSYNACK(data, addr):
                print("Received the SYNC packet successfully")
                print("Sent the SYNC+ACK packet")
                return self.recvACKclient_sendID(data, addr)
            return -1
        except socket.timeout:
            return -1
        except Exception as e:
            print(f"Error receiving UDP packet: {e}")
            return -1

        

    def client_connect_protocol(self):
        """Handles the connection protocol with clients."""
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
        """Handles communication with a connected client."""
        conn = self.connected_clients[client_id][1]
        client_address = self.connected_clients[client_id][0]
        print(f"Connected to client {client_id} at {client_address}")
        try:
            while True:
                data = conn.recv(1024)
                if not data:  # Client disconnected
                    break
                message = data.decode()
                print(f"Received message from client {client_address}: {message}")
                # Process the client message (Update player data and send other player info)
                self.process_player_data(client_id, message)  # Pass the socket object
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            # Clean up when client disconnects
            print(f"Client {client_address} disconnected.")
            if id in self.connected_clients.keys():
                del self.connected_clients[client_id]
            if id in self.players_data.keys():
                del self.players_data[client_id]
            conn.close()

    def process_move(self, data, id):
        str_data = data.decode()
        str_data = str_data.split(" ")[-1]
        try:
            str_data = str_data.split(";")
            data_x = int(str_data[0]); data_y = int(str_data[1])
            self.players_data[id]["x"] = data_x; self.players_data[id]["y"] = data_y

        except Exception as e:
            print(f"Error processing move data for {id}: {e}")




    def process_player_data(self, client_id, message):
        try:
            self.players_data[client_id] = json.loads(message)
            # Prepare data of other players to send to the client (excluding the client's own data)
            other_players_data = []
            for id, data in self.players_data.items():
                if id != client_id:
                    copy_data = data.copy()
                    copy_data["id"] = id
                    other_players_data.append(copy_data)
            # Convert to JSON string and send
            other_players_data_str = json.dumps(other_players_data)
            self.connected_clients[client_id][1].send(other_players_data_str.encode())
            print(f"Sent other players' data to client {client_id}")
        except Exception as e:
            print(f"Error processing player data for {client_id}: {e}")

    def run(self):
        """Runs the sub-server."""
        # Start load balancer connection
        lb_thread = threading.Thread(target=self.lb_connect_protocol)
        lb_thread.start()
        lb_thread.join() #Wait for the thread to establish a connection with the load balancer

        if self.is_connected_to_lb:
            client_thread = threading.Thread(target=self.client_connect_protocol)
            client_thread.start()
        else:
            print("Load balancer not properly connected, not listening to clients.")

if __name__ == "__main__":
    server = SubServer()
    server.run()

import socket
import json
import threading
import time

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
        self.load_balancer_address = (0, LB_PORT)
        self.connected_clients = {}  # Store connected clients' addresses (IP -> Socket object)
        self.is_connected_to_lb = False
        self.players_data = {}  # Dictionary to store player information (IP -> player_info)
        self.udp_socket.settimeout(4) # Set a timeout for UDP socket
        self.id = 0

    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address

    def recv_id(self):
        data = self.lb_socket.recv(1024)
        str_data = data.decode()
        if str_data.startswith("ID"):
            self.id = int(str_data.split(" ")[-1])
            print("Received ID:", self.id)
            return True
        return False

    def lb_connect_protocol(self):
        """Handles the connection protocol with the load balancer."""
        print("Listening on UDP for load balancer on", self.get_ip_address())
        while not self.is_connected_to_lb:
            try:
                data, _ = self.udp_socket.recvfrom(1024)
                print("Received UDP packet: ", data.decode())
                if self.readSYNCpacket(data):
                    self.sendSYNCACK()
                    if self.recvACK():
                        if self.recv_id():
                            self.is_connected_to_lb = True
            except socket.timeout:
                print("No UDP packet received within timeout period")
            except Exception as e:
                print(f"Error receiving UDP packet: {e}")
                if self.lb_socket:
                    self.lb_socket.shutdown(socket.SHUT_RDWR)
                    self.lb_socket.close()
            
    
    def readSYNCpacket(self, data):
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

    def sendSYNCACK(self):
        self.lb_socket.send(SYN_ACK.encode())

    def recvACK(self):
        data = self.lb_socket.recv(1024).decode()
        if data.startswith(ACK):
            print("Received ACK")
            self.id = int(data.split(";")[-1])
            print("ID:", self.id)
            return True
        return False

    def client_connect_protocol(self):
        """Handles the connection protocol with clients."""
        print("Listening for clients on", self.server_address)
        while self.is_connected_to_lb:
            conn, client_address = self.server_socket.accept()
            print(f"Client {client_address} connected.")
            self.connected_clients[client_address[1]] = conn  # Store the socket object
            client_thread = threading.Thread(target=self.handle_client, args=(conn, client_address))
            client_thread.start()
            print(f"Started thread for client {client_address}")
            print("Connected clients:", self.connected_clients.keys())
        print("Not listening to clients anymore.")

    def handle_client(self, conn, client_address):
        """Handles communication with a connected client."""
        try:
            while True:
                data = conn.recv(1024)
                if not data:  # Client disconnected
                    break
                message = data.decode()
                print(f"Received message from client {client_address}: {message}")
                # Process the client message (Update player data and send other player info)
                self.process_player_data(conn, message, client_address)  # Pass the socket object
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            # Clean up when client disconnects
            print(f"Client {client_address} disconnected.")
            if client_address[1] in self.connected_clients:
                del self.connected_clients[client_address[1]]  # Remove the socket
            if client_address[1] in self.players_data:
                del self.players_data[client_address[1]]
            conn.close()

    def process_player_data(self, conn, player_data_str, client_address):
        """
        Receives player data, updates the player data dictionary,
        and sends a list of other players' information to the client.
        """
        try:
            player_data = json.loads(player_data_str)
            # Update player data in the dictionary
            self.players_data[client_address[1]] = player_data
        
            # Prepare data of other players to send to the client (excluding the client's own data)
            other_players_data = []
            for port, data in self.players_data.items():
                if port != client_address[1]:
                    copy_data = data.copy()
                    copy_data["port"] = port
                    other_players_data.append(copy_data)
            # Convert to JSON string and send
            other_players_data_str = json.dumps(other_players_data)
            conn.send(other_players_data_str.encode())
            print(f"Sent other players' data to client {client_address}")
        except json.JSONDecodeError:
            print(f"Error decoding player data from {client_address}")
        except Exception as e:
            print(f"Error processing player data for {client_address}: {e}")

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

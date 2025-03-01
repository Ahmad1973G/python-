import socket
import json
import threading
import time

# Configuration
LB_IP = '127.0.0.1'  # Roy's Computer, temporary fix #MUST BE 127.0.0.1 when both run on the same computer
LB_PORT = 5000  # Replace with the load balancer port
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5001  # Let the OS assign a port
SERVER_ID = 1  # Unique identifier for this server

# Protocol Messages
SYN = "SYNC CODE 1"
SYN_ACK = "SYNC+ACK CODE 1"
ACK = "ACK CODE 2"

class SubServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Changed to TCP
        self.lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (SERVER_IP, SERVER_PORT)
        self.server_socket.bind(self.server_address)
        self.server_socket.listen()  # Listen for incoming connections
        self.load_balancer_address = (LB_IP, LB_PORT)
        self.connected_clients = {}  # Store connected clients' addresses (IP -> Socket object)
        self.is_connected_to_lb = False
        self.players_data = {}  # Dictionary to store player information (IP -> player_info)

    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address

    def lb_connect_protocol(self):
        """Handles the connection protocol with the load balancer."""
        self.lb_socket.connect(self.load_balancer_address)

        while not self.is_connected_to_lb:
            # Listen for SYN from Load Balancer
            print("Listening for SYN from load balancer...")
            try:
                data = self.lb_socket.recv(1024)
                message = data.decode()
                peer_address = self.lb_socket.getpeername()
                if message == SYN and peer_address[0] == LB_IP:  # Changed from self.lb_socket[0]
                    print(f"Received SYN from load balancer at {peer_address}")
                    # Send SYN+ACK
                    self.lb_socket.send(SYN_ACK.encode())
                    print(f"Sent SYN+ACK to load balancer at {peer_address}")
                    # Wait for ACK
                    data = self.lb_socket.recv(1024)
                    message = data.decode()
                    if message == ACK and peer_address[0] == LB_IP:  # Changed from self.lb_socket[0]
                        print(f"Received ACK from load balancer at {peer_address}")
                        self.is_connected_to_lb = True
                        print("Successfully connected to load balancer.")
                    else:
                        print("Unexpected message from load balancer. Retrying...")
                else:
                    print("Unexpected message or incorrect load balancer IP. Retrying...")

            except Exception as e:
                print(f"Exception occurred while trying to connect to Load Balancer, exiting loop: {e}")

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
            print("Connected clients:", self.connected_clients)
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
            other_players_data = [data for port, data in self.players_data.items() if port != client_address[1]]
                
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

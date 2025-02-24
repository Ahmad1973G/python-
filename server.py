import socket
import json
import threading
import time

# Configuration
LB_IP = 'Your_Load_Balancer_IP'  # Replace with the load balancer's IP
LB_PORT = 5000  # Replace with the load balancer port
SERVER_PORT = 0  # Let the OS assign a port
CLIENT_SYN_PORT = 6000 # The port that clients will broadcast SYN packets
SERVER_ID = 1  # Unique identifier for this server


# Protocol Messages
SYN = "SYN"
SYN_ACK = "SYN+ACK"
ACK = "ACK"


class SubServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (self.get_ip_address(), SERVER_PORT)
        self.server_socket.bind(self.server_address)
        self.server_socket.listen(5)
        self.server_address = (self.get_ip_address(), self.server_socket.getsockname()[1])
        self.load_balancer_address = (LB_IP, LB_PORT)
        self.connected_clients = {}  # Store connected clients' addresses
        self.is_connected_to_lb = False

    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address

    def lb_connect_protocol(self):
        """Handles the connection protocol with the load balancer."""
        while not self.is_connected_to_lb:
            # Listen for SYN from Load Balancer
            print("Listening for SYN from load balancer...")
            self.server_socket.settimeout(10)  # Set a timeout to avoid blocking
            try:
                conn, address = self.server_socket.accept()
                data = conn.recv(1024)
                message = data.decode()
                if message == SYN and address[0] == LB_IP:
                    print(f"Received SYN from load balancer at {address}")
                    # Send SYN+ACK 
                    conn.send(SYN_ACK.encode())
                    print(f"Sent SYN+ACK to load balancer at {address}")
                    # Wait for ACK
                    data = conn.recv(1024)
                    message = data.decode()
                    if message == ACK and address[0] == LB_IP:
                        print(f"Received ACK from load balancer at {address}")
                        self.is_connected_to_lb = True
                        print("Successfully connected to load balancer.")
                    else:
                        print("Unexpected message from load balancer. Retrying...")
                else:
                    print("Unexpected message or incorrect load balancer IP. Retrying...")
                conn.close()
            except socket.timeout:
                print("Timeout waiting for SYN. Retrying...")

    def handle_client(self, conn, client_address):
        """Handles communication with a connected client."""
        try:
            while self.connected_clients[client_address]:
                data = conn.recv(1024)
                message = data.decode()
                print(f"Received message from client {client_address}: {message}")
                # Process the client message
                response = f"Server received: {message}"  # Example response
                conn.send(response.encode())
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            # Clean up when client disconnects
            print(f"Client {client_address} disconnected.")
            del self.connected_clients[client_address]
            conn.close()

    def run(self):
        """Runs the sub-server."""
        # Start load balancer connection
        lb_thread = threading.Thread(target=self.lb_connect_protocol)
        lb_thread.start()
        # Start client connection
        client_thread = threading.Thread(target=self.client_connect_protocol)
        client_thread.start()

    def client_connect_protocol(self):
        """Handles the connection protocol with clients."""
        while True:
            conn, client_address = self.server_socket.accept()
            print(f"Client {client_address} connected.")
            self.connected_clients[client_address] = True
            client_thread = threading.Thread(target=self.handle_client, args=(conn, client_address))
            client_thread.start()


if __name__ == "__main__":
    server = SubServer()
    server.run()
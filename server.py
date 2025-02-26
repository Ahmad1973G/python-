import socket
import json
import threading
import time

# Configuration
LB_IP = 'Load_Balancer_IP'  # Replace with the load balancer's IP
LB_PORT = 5000  # Replace with the load balancer port
SERVER_PORT = 0  # Let the OS assign a port
CLIENT_SYN_PORT = 6000  # The port that clients will broadcast SYN packets
SERVER_ID = 1  # Unique identifier for this server

# Protocol Messages
SYN = "SYN"
SYN_ACK = "SYN+ACK"
ACK = "ACK"


class SubServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Changed to TCP
        self.server_address = (self.get_ip_address(), SERVER_PORT)
        self.server_socket.bind(self.server_address)
        self.server_socket.listen(5)  # Listen for incoming connections
        self.server_address = (self.get_ip_address(), self.server_socket.getsockname()[1])
        self.load_balancer_address = (LB_IP, LB_PORT)
        self.connected_clients = {}  # Store connected clients' addresses (IP:PORT -> Socket object)
        self.is_connected_to_lb = False
        self.player_data = {}  # Dictionary to store player information (IP:PORT -> player_info)

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
                    conn.send(SYN_ACK.encode())  # Use conn.send() instead of self.server_socket.sendto()
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
                conn.close()  # Close the connection after the protocol
            except socket.timeout:
                print("Timeout waiting for SYN. Retrying...")

    def client_connect_protocol(self):
        """Handles the connection protocol with clients."""
        while True:
            conn, client_address = self.server_socket.accept()
            print(f"Client {client_address} connected.")
            self.connected_clients[client_address] = conn  # Store the socket object
            client_thread = threading.Thread(target=self.handle_client, args=(conn, client_address))
            client_thread.start()

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
            if client_address in self.connected_clients:
                del self.connected_clients[client_address]  # Remove the socket
            if client_address in self.player_data:
                del self.player_data[client_address]
            conn.close()  # Close the connection

    def process_player_data(self, conn, player_data_str, client_address):
        """
        Receives player data, updates the player data dictionary,
        and sends a list of other players' information to the client.
        """
        try:
            player_data = json.loads(player_data_str)
            # Update player data in the dictionary
            self.player_data[client_address] = player_data

            # Prepare data of other players to send to the client (excluding the client's own data)
            other_players_data = [data for addr, data in self.player_data.items() if addr != client_address]

            # Convert the list to a JSON string
            other_players_data_str = json.dumps(other_players_data)

            # Send the other players' data back to the client
            conn.send(other_players_data_str.encode())  # Send using the connection socket
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

        # Start client connection
        client_thread = threading.Thread(target=self.client_connect_protocol)
        client_thread.start()


if __name__ == "__main__":
    server = SubServer()
    server.run()

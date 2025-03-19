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
    """
    A class to represent a sub-server that connects to a load balancer and handles client connections.

    Attributes:
    -----------
    server_socket : socket.socket
        TCP socket for server-client communication.
    lb_socket : socket.socket
        TCP socket for server-load balancer communication.
    udp_socket : socket.socket
        UDP socket for broadcasting and receiving messages.
    server_address : tuple
        IP address and port of the server.
    load_balancer_address : tuple
        IP address and port of the load balancer.
    connected_clients : dict
        Dictionary to store connected clients' addresses and sockets.
    is_connected_to_lb : bool
        Flag to check if the server is connected to the load balancer.
    players_data : dict
        Dictionary to store player information.
    id : int
        Unique identifier for the server.
    ids : list
        List of assigned client IDs.
    updated_elements : dict
        Dictionary to store updated player data.
    """

    def __init__(self):
        """
        Initializes the SubServer with necessary sockets and configurations.
        """
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
        self.udp_socket.settimeout(4)  # Set a timeout for UDP socket
        self.id = 0
        self.ids = []
        self.updated_elements = {}

    def get_ip_address(self):
        """
        Gets the IP address of the current machine.

        Returns:
        --------
        str
            The IP address of the current machine.
        """
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address

    def lb_connect_protocol(self):
        """
        Handles the connection protocol with the load balancer.
        """
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
        """
        Reads the SYN message from the load balancer and attempts to connect.

        Parameters:
        -----------
        data : bytes
            The data received from the load balancer.

        Returns:
        --------
        bool
            True if the connection is successful, False otherwise.
        """
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
        """
        Sends the SYN+ACK message to the load balancer.
        """
        self.lb_socket.send(SYN_ACK.encode())

    def recvACKLB(self):
        """
        Receives the ACK message from the load balancer.

        Returns:
        --------
        bool
            True if the ACK message is received, False otherwise.
        """
        data = self.lb_socket.recv(1024).decode()
        if data.startswith(ACK):
            print("Received ACK")
            self.id = int(data.split(";")[-1])
            print("ID:", self.id)
            return True
        return False

    def recvSYNclient_sendSYNACK(self, data, addr):
        """
        Receives the SYN message from a client and sends the SYN+ACK message.

        Parameters:
        -----------
        data : bytes
            The data received from the client.
        addr : tuple
            The address of the client.

        Returns:
        --------
        bool
            True if the SYN message is received, False otherwise.
        """
        str_data = data.decode()
        if str_data == "SYNC CODE 69":
            self.udp_socket.sendto(f"SYNC+ACK CODE 69 {self.server_address[0]};{self.server_address[1]}".encode(), addr)
            return True
        return False

    def recvACKclient_sendID(self, data, addr):
        """
        Receives the ACK message from a client and sends the ID message.

        Parameters:
        -----------
        data : bytes
            The data received from the client.
        addr : tuple
            The address of the client.

        Returns:
        --------
        int
            The assigned client ID.
        """
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
        """
        Handles the initial connection protocol with clients.

        Returns:
        --------
        int
            The assigned client ID or -1 if the connection fails.
        """
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
        """
        Handles the connection protocol with clients.
        """
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
        """
        Handles communication with a connected client.

        Parameters:
        -----------
        client_id : int
            The ID of the connected client.
        """
        conn = self.connected_clients[client_id][1]
        client_address = self.connected_clients[client_id][0]
        print(f"Connected to client {client_id} at {client_address}")
        try:
            while True:
                data = conn.recv(1024)
                if not data:  # Client disconnected
                    break
                message = data.decode()
                # Process the client message (Update player data and send other player info)
                self.process_player_data(client_id, message)  # Pass the socket object
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            # Clean up when client disconnects
            print(f"Client {client_address} disconnected.")
            del self.connected_clients[client_id]
            del self.players_data[client_id]
            conn.close()

    def process_player_data(self, client_id, message: str):
        """
        Processes the player data received from a client.

        Parameters:
        -----------
        client_id : int
            The ID of the client.
        message : str
            The message received from the client.
        """
        try:
            message = json.loads(message)
            for key in message.keys():
                self.players_data[client_id][key] = message[key]
                self.updated_elements[client_id][key] = message[key]

            for key in self.players_data[client_id].keys():
                if key not in self.updated_elements[client_id].keys():
                    self.updated_elements[client_id][key] = None

            # Prepare data of other players to send to the client (excluding the client's own data)
            other_players_data = []
            for id, data in self.updated_elements.items():
                if id != client_id:
                    copy_data = data.copy()
                    copy_data["id"] = id
                    other_players_data.append(copy_data)

            self.updated_elements[client_id] = {} # Clear the updated elements
            # Convert to JSON string and send
            other_players_data_str = json.dumps(other_players_data)
            self.connected_clients[client_id][1].send(other_players_data_str.encode())
        except Exception as e:
            print(f"Error processing player data for {client_id}: {e}")

    def run(self):
        """
        Runs the sub-server.
        """
        # Start load balancer connection
        lb_thread = threading.Thread(target=self.lb_connect_protocol)
        lb_thread.start()
        lb_thread.join()  # Wait for the thread to establish a connection with the load balancer

        if self.is_connected_to_lb:
            self.client_connect_protocol()
        else:
            print("Load balancer not properly connected, not listening to clients.")

if __name__ == "__main__":
    server = SubServer()
    server.run()
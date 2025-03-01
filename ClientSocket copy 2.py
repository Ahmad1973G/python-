import socket
import json
import threading
import random
import time

SERVER_IP = '127.0.0.1'
SERVER_PORT = 5001  # Let the OS assign a port

class ClientServer:
    def __init__(self):
        self.IP = 0
        self.PORT = 0
        self.server = ()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.time = time.time()

    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    
    def createSYNCpacket(self):
        packet = "SYNC CODE 69"
        return packet.encode()
    
    def read_SYN_and_send_SA(self, conn):
        data = conn.recv(1024)
        str_data = data.decode()
        if str_data == 'SYNC+ACK CODE 420':
            conn.send(f"ACK CODE 999 IP.{self.IP} PORT.{self.PORT}".encode())
            print("Received the SYN+ACK packet successfully")
            print("Sent the ACK packet")
            return True
        return False
    def create_client_properties(self):
        properties = {
            "x": int(random.random() * 38400),
            "y": int(random.random() * 34560),
            "attack": int(random.random() * 300),
            "health": 100,
        }
        return properties

    def read_ACK(self, conn):
        data = conn.recv(1024)
        str_data = data.decode()
        if str_data == 'ACK CODE 584':
            print("Received the ACK packet successfully from IP: ", conn.getpeername()[0], " Port: ", conn.getpeername()[1])
            self.server = conn.getpeername()
            return True
        else:
            return False

    def send_data(self, data):
        try:
            self.socket.send(data.encode())
        except socket.error as e:
            print(f"Error sending data: {e}")
    
    def receive_data(self):
        data = self.socket.recv(1024)
        return data.decode()
    
    def connect(self, IP, PORT):
        self.server = (IP, PORT)
        while True:
            try:
                self.socket.connect(self.server)
                break
            except Exception as e:
                print("Connection failed, trying again, error:", e)
        print(f"Connected to {IP} on port {PORT}")
        self.IP = self.socket.getsockname()[0]
        self.PORT = self.socket.getsockname()[1]
    
    def run_conn(self, data):
        print("Sending data...")
        self.send_data(data)
        print("Data sent.")
        response = self.receive_data()
        print("Received data.")
        response = json.loads(response)
        return response

    def run(self):
        start_time = time.time()
        while True: 
            if time.time() - start_time > 2:
                result = self.run_conn(json.dumps(self.create_client_properties()))
                print(result)
                start_time = time.time()


def main():
    client = ClientServer()
    client.connect(SERVER_IP, SERVER_PORT)
    client.run()

if __name__ == "__main__":
    main()
# This is the client socket that connects to the server and sends data to it.
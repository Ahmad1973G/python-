import socket
import json
import threading
import time

SERVER_PORT = 5003  # Let the OS assign a port


class ClientServer:
    def __init__(self):
        self.server = None
        self.IP = self.get_ip_address()
        self.PORT = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.settimeout(5)
        self.id = 0

    def broadcast_packet(self, packet, port):
        self.udp_socket.sendto(packet, ('255.255.255.255', port))

    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address

    def createSYNCpacket(self):
        packet = "SYNC CODE 69"
        return packet.encode()

    def read_ACK(self, conn):
        data = conn.recv(1024)
        str_data = data.decode()
        if str_data == 'ACK CODE 584':
            print("Received the ACK packet successfully from IP: ", conn.getpeername()[0], " Port: ",
                  conn.getpeername()[1])
            self.server = conn.getpeername()
            return True
        else:
            return False

    def recSYNCACK_sendACK(self):
        while True:
            while True:
                try:
                    data, addr = self.udp_socket.recvfrom(1024)
                    str_data = data.decode()
                    break
                except socket.timeout:
                    print("Sending SYNC packet again...")
                    self.broadcast_packet(self.createSYNCpacket(), SERVER_PORT)
                except Exception as e:
                    print("Error receiving SYNC+ACK packet:", e)

            if str_data.startswith("SYNC+ACK CODE 69"):
                self.server = (str_data.split(" ")[-1].split(";")[0],
                               int(str_data.split(" ")[-1].split(";")[1]))
                try:
                    self.socket.connect(self.server)
                    print(f"Connected to {self.server[0]} on port {self.server[1]}")
                    self.PORT = self.socket.getsockname()[1]
                    return True
                except Exception as e:
                    print("Error connecting to server:", e)
            return False

    def recv_ID(self):
        data = self.socket.recv(1024)
        str_data = data.decode()
        if str_data.startswith("ID CODE 69"):
            return int(str_data.split(" ")[-1])
        return -1

    def connect(self):
        self.broadcast_packet(self.createSYNCpacket(), SERVER_PORT)
        print("Sent the SYNC packet")
        if self.recSYNCACK_sendACK():
            print("Received the SYNC+ACK packet successfully")
            print("Sent the ACK packet")
            self.id = self.recv_ID()
            print("Received the ID packet, ID:", self.id)
            return self.id

    def send_data(self, data):
        try:
            self.socket.send(data.encode())
        except socket.error as e:
            print(f"Error sending data: {e}")

    def receive_data(self):
        data = self.socket.recv(1024)
        return data.decode()

    def run_conn(self, data):
        # print("Sending data...")
        self.send_data(data)
        # print("Data sent.")
        response = self.receive_data()
        # print("Received data.")
        response = json.loads(response)
        return response
# This is the client socket that connects to the server and sends data to it.
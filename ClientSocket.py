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

    def MoveServer(self, data):
        try:
            ip = int(data)
            port = self.server[1]
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, port))
            data = self.socket.recv(1024)
            str_data = data.decode()
            if str_data.startswith("ID"):
                self.socket.send(f"ID CODE 69;{self.id}".encode())
                print("Received the ID packet successfully")
                print("Sent the ID packet")
                self.server = (ip, port)
                return True
            return False
        except Exception as e:
            print("Error connecting to server:", e)
            return False

    def protocol_check(self, data: str):
        if data == "ACK":
            print("ACK received")
            return True

        if data.startswith("MOVING"):
            if not self.MoveServer(data):
                print("Error moving server")
                return False
            print("Server moved successfully")
            return True

    def sendMOVE(self, x, y):
        # Add newline delimiter to separate messages
        self.socket.send(f"MOVE {x};{y}".encode())
        message = self.socket.recv(1024)
        message = message.decode()
        if self.protocol_check(message):
            print("Move sent successfully")

    def sendSHOOT(self, start_x, start_y, end_x, end_y, weapon):
        self.socket.send(f"SHOOT {start_x};{start_y};{end_x};{end_y};{weapon}".encode())
        message = self.socket.recv(1024)
        message = message.decode()
        if self.protocol_check(message):
            print("Shoot sent successfully")

    def sendANGLE(self, angle):
        self.socket.send(f"ANGLE {angle}".encode())
        message = self.socket.recv(1024)
        message = message.decode()
        if self.protocol_check(message):
            print("Angle sent successfully")

    def sendDAMAGE(self, damage):
        self.socket.send(f"DAMAGE {damage}".encode())
        message = self.socket.recv(1024)
        message = message.decode()
        if self.protocol_check(message):
            print("Damage sent successfully")

    def sendPOWER(self, power):
        self.socket.send(f"POWER {power}".encode())
        message = self.socket.recv(1024)
        message = message.decode()
        if self.protocol_check(message):
            print("Power sent successfully")

    def requestDATA(self):
        try:
            self.socket.send("REQUEST".encode())
            data = self.socket.recv(1024)
            if not data:
                return {}

            data = data.decode()
            if data == "WARNING":
                return "WARNING"
            elif data == "KICK":
                self.socket.close()
                return "KICK"
            else:
                # Assuming the data is just JSON without prefix
                return json.loads(data)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return {}
        except socket.error as e:
            print(f"Socket error: {e}")
            return {}

    def requestDATAFULL(self):
        try:
            self.socket.send("REQUESTFULL".encode())
            data = self.socket.recv(1024)
            if not data:
                return None

            data = data.decode()
            if data == "WARNING":
                return "WARNING"
            elif data == "KICK":
                self.socket.close()
                return "KICK"
            else:
                # Assuming the data is just JSON without prefix
                return json.loads(data)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return {}
        except socket.error as e:
            print(f"Socket error: {e}")
            return  {}

    def login(self, user, password):
        self.socket.send(f"LOGIN {user};{password}".encode())
        message = self.socket.recv(1024)
        message = message.decode()
        if message == "LOGIN":
            print("Login successful")
            return True
        else:
            print("Login failed, error:", message)
            return False
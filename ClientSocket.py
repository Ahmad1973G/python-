import base64
import socket
import json
import threading

from RSA import RSA
from AES import AES

SERVER_PORT = 5004


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
        self.chat_sequence = 0

        self.lock = threading.Lock()
        self.aes = AES()

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
                self.server = (addr[0],
                               int(str_data.split(" ")[-1].split(";")[1]))
                try:
                    print("Connecting to server at IP:", self.server[0], "Port:", self.server[1])
                    self.socket.connect(self.server)
                    print(f"Connected to {self.server[0]} on port {self.server[1]}")
                    self.PORT = self.socket.getsockname()[1]
                    return True
                except Exception as e:
                    print("Error connecting to server:", e)
            return False

    def recv_ID(self):
        packet_data = self.socket.recv(1024)
        str_data = packet_data.decode()
        if str_data.startswith("ID CODE 69"):
            return int(str_data.split(" ")[-1])
        return -1


    def recvRsaPublicKeySendAes(self):
        packet_data = self.socket.recv(1024)
        str_data = packet_data.decode()
        if str_data.startswith("RSA PUBLIC"):
            str_data = str_data.split("|", 1)[-1]
            data = str_data.encode()
            rsa = RSA()
            aes_key = self.aes.key
            print("AES key generated:", base64.b64encode(aes_key).decode())
            data_to_send = rsa.encrypt_aes_key(aes_key, rsa.load_public_key_from_bytes(data))
            print("Encrypted AES key with RSA public key len: ", len(data_to_send))
            self.socket.send(data_to_send)


    def connect(self):
        self.broadcast_packet(self.createSYNCpacket(), SERVER_PORT)
        print("Sent the SYNC packet")
        if self.recSYNCACK_sendACK():
            print("Received the SYNC+ACK packet successfully")
            self.id = self.recv_ID()
            print("Received the ID packet, ID:", self.id)
            if self.id != -1:
                print("Sent the ID packet")
                self.recvRsaPublicKeySendAes()
                print("Received RSA public key and sent AES key")
                return self.id
            else:
                print("Failed to receive ID packet")
        return None

    def MoveServer(self, data):
        try:
            ip = int(data)
            port = self.server[1]
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, port))
            data = self.socket.recv(1024)
            str_data = self.aes.decrypt_message(data)
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
            return True

        if data.startswith("MOVING"):
            if not self.MoveServer(data):
                print("Error moving server")
                return False
            print("Server moved successfully")
            return True
        return None

    def sendBOTDAMAGE(self, damage: int, bot_id: int):
        with self.lock:
            data = self.aes.encrypt_message(f"DAMAGE {bot_id};{damage}")
            self.socket.send(data)
            message = self.socket.recv(1024)
        message = self.aes.decrypt_message(message)
        if self.protocol_check(message):
            print("Damage sent successfully")

    def sendMOVE(self, x, y, weapon: int, angle, flag):
        # Add newline delimiter to separate messages
        if flag:
            with self.lock:
                data = self.aes.encrypt_message(f"MOVE {x};{y};{weapon}")
                self.socket.send(data)
                message = self.socket.recv(1024)
            message = self.aes.decrypt_message(message)
            if self.protocol_check(message):
                print("Move sent successfully")
        else:
            with self.lock:
                self.socket.send(self.aes.encrypt_message(f"ANGLE {angle}"))
                message = self.socket.recv(1024)
            message = self.aes.decrypt_message(message)
            if self.protocol_check(message):
                pass
            # print("Angle sent successfully")

    def sendSHOOT(self, start_x, start_y, end_x, end_y, weapon):
        with self.lock:
            self.socket.send(self.aes.encrypt_message(f"SHOOT {start_x};{start_y};{end_x};{end_y};{weapon}"))
            message = self.socket.recv(1024)
        message = self.aes.decrypt_message(message)
        if self.protocol_check(message):
            print("Shoot sent successfully")

    def sendANGLE(self, angle):
        with self.lock:
            self.socket.send(self.aes.encrypt_message(f"ANGLE {angle}"))
            message = self.socket.recv(1024)
        message = self.aes.decrypt_message(message)
        if self.protocol_check(message):
            pass
            # print("Angle sent successfully")

    def sendHEALTH(self, health: int):
        with self.lock:
            self.socket.send(self.aes.encrypt_message(f"HEALTH {health}"))
            message = self.socket.recv(1024)
        message = self.aes.decrypt_message(message)
        if self.protocol_check(message):
            print("Damage sent successfully")

    def sendPOWER(self, power):
        with self.lock:
            self.socket.send(self.aes.encrypt_message(f"POWER {power}"))
            message = self.socket.recv(1024)
        message = self.aes.decrypt_message(message)
        if self.protocol_check(message):
            print("Power sent successfully")

    def sendMONEY(self, money):
        with self.lock:
            self.socket.send(self.aes.encrypt_message(f"MONEY {money}"))
            message = self.socket.recv(1024)
        message = self.aes.decrypt_message(message)
        if self.protocol_check(message):
            print("Power sent successfully")

    def sendAMMO(self, ammo):
        with self.lock:
            self.socket.send(self.aes.encrypt_message(f"AMMO {ammo}"))
            message = self.socket.recv(1024)
        message = self.aes.decrypt_message(message)
        if self.protocol_check(message):
            print("Power sent successfully")

    def sendINVENTORY(self, inventory):
        with self.lock:
            self.socket.send(self.aes.encrypt_message(f"INVENTORY {inventory[0]};{inventory[1]};"
                         f"{inventory[2]};{inventory[3]};{inventory[4]}"))
            message = self.socket.recv(1024)
        message = self.aes.decrypt_message(message)
        if self.protocol_check(message):
            print("Inventory sent successfully")


    def sendBOOM(self, x, y, brange):
        with self.lock:
            self.socket.send(self.aes.encrypt_message(f"BOMB {x};{y};{brange}\n"))
            message = self.socket.recv(1024)
        message = self.aes.decrypt_message(message)
        if message == "ACK":
            print("SOCKET; boom sent successfully")
        else:
            print("SOCKET; Failed to send boom, error:", message)

    def sendCHAT(self, message):
        with self.lock:
            self.socket.send(f"CHAT SEND {message}".encode())
            message = self.socket.recv(1024)
        message = self.aes.decrypt_message(message)
        if message == "ACK":
            print("SOCKET; chat sent successfully")
        else:
            print("SOCKET; Failed to send chat, error:", message)

    def recvCHAT(self):
        with self.lock:
            self.socket.send(self.aes.encrypt_message(f"CHAT RECV {self.chat_sequence}"))
            message = self.socket.recv(1024)
        message = self.aes.decrypt_message(message)
        if message == "UPDATED":
            print("SOCKET; chat already updated")
            return True
        messages = message.split(";")
        self.chat_sequence = int(messages[0])
        chat_message = messages[1]
        chat_messages = json.loads(chat_message)
        print("SOCKET; chat received successfully")
        return chat_messages


    def requestDATA(self):
        try:
            with self.lock:
                self.socket.send(self.aes.encrypt_message("REQUEST"))
                data = self.socket.recv(100000)
            if not data:
                return None

            data = self.aes.decrypt_message(data)
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
            return None
        except socket.error as e:
            print(f"Socket error: {e}")
            return None

    def requestDATAFULL(self):
        try:
            with self.lock:
                data = self.aes.encrypt_message("REQUESTFULL")
                self.socket.send(data)
                data = self.socket.recv(100000)
            if not data:
                return None

            data = self.aes.decrypt_message(data)
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
            print(data)
            return None
        except socket.error as e:
            print(f"Socket error: {e}")
            return None

    def login(self, user, password):
        with self.lock:
            data = self.aes.encrypt_message(f"LOGIN {user};{password}")
            self.socket.send(data)
            print("user login...")
            message = self.socket.recv(1024)
        print("Received message:", message)
        message = self.aes.decrypt_message(message)
        if message.startswith("SUCCESS CODE LOGIN"):
            try:
                # Extract JSON data and ensure proper formatting
                player_data = message.split(" ", maxsplit=3)[-1]
                # Convert single quotes to double quotes for valid JSON
                player_data = player_data.replace("'", '"')
                player_data = json.loads(player_data)
                return True, player_data
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Raw player data: {player_data}")
                return False, "Invalid server response format"
        if message.startswith("FAILED CODE LOGIN"):
            error = message.split(" ", maxsplit=3)[-1]
            print("Register failed, error:", error)
            return False, error
        return False, "Unknown error"

    def register(self, user, password):
        with self.lock:
            data = self.aes.encrypt_message(f"REGISTER {user};{password}")
            self.socket.send(data)
            print("Registering user...")
            message = self.socket.recv(1024)
        print("Received message:", message)
        message = self.aes.decrypt_message(message)
        if message.startswith("SUCCESS CODE REGISTER"):
            try:
                # Extract JSON data and ensure proper formatting
                player_data = message.split(" ", maxsplit=3)[-1]
                # Convert single quotes to double quotes for valid JSON
                player_data = player_data.replace("'", '"')
                player_data = json.loads(player_data)
                return True, player_data
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Raw player data: {player_data}")
                return False, "Invalid server response format"
        if message.startswith("FAILED CODE REGISTER"):
            error = message.split(" ", 3)[-1]
            print("Register failed, error:", error)
            return False, error
        return False, "Unknown error"

if __name__ == "__main__":
    client = ClientServer()
    client.connect()
    print("Client ID:", client.id)
    # Example usage
    success, data = client.login("fg", "1234")
    if success:
        print("Login successful, player data:", data)
    else:
        print("Login failed:", data)

    print(client.sendMOVE(100, 200, 1, 45, True))
import socket
import client_test

class ClientServer:
    def __init__(self):
        self.IP = self.get_ip_address()
        self.PORT = 0
        self.server = ()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
        self.socket.connect(self.server)
        print(f"Connected to {IP} on port {PORT}")


def main():
    client = ClientServer()
    while True:
        try:
            client.connect(1, 1)
            break
        except:
            print("Connection failed, trying again")

    data = client_test.comp_data()
    client.send_data(data)
    client.receive_data() 
    client_test.get_data(client.receive_data())
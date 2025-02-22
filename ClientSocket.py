import socket

class ClientServer:
    def __init__(self):
        self.IP = self.get_ip_address()
        self.PORT = 0
        self.server = ()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def get_ip_address():
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    
    def createSYNCpacket(self):
        packet = "SYNC CODE 69"
        return packet.encode()
    
    def read_SYN_and_send_SA(self, data):
        str_data = data.decode()
        if (str_data == 'SYNC+ACK CODE 420'):
            self.socket.sendto(f"ACK CODE 999 IP.{self.IP} PORT.{self.PORT}".encode(), (self.IP, self.PORT))
            print("Received the SYN+ACK packet successfully")
            print("Sent the ACK packet")
            return True
        
        return False
    
    def read_ACK(self, data, addr):
        str_data = data.decode()
        if (str_data == 'ACK CODE 584'):
            print("Received the ACK packet successfully from IP: ", addr[0], " Port: ", addr[1])
            self.server = addr
            return True
        else:
            return False

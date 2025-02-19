import socket

class LoadBalancer:
    def __init__(self):
        self.LbIP = self.get_ip_adress()
        self.LbPORT = 0
        self.servers = []

    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
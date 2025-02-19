import socket
import json

# List of server IPs

# Load balancer port

# Map dimensions
MAP_WIDTH = 38400
MAP_HEIGHT = 34560
# Maximum attack range
MAX_ATTACK = 300

def main():
    """
    Main function to start sniffing packets.
    
    Args:
        server_borders (tuple): The borders of the server.
    """
    server_borders = (MAP_WIDTH / 2, MAP_HEIGHT / 2)
    LB_PORT = 0
    LB_IP = get_ip_address()
    SERVER_IPS_PORTS = []
    start_protocol()
    sniff_packets(server_borders, LB_PORT, LB_IP, SERVER_IPS_PORTS)

def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

def sniff_packets(server_borders):
    """
    Sniffs packets using the socket module.
    
    Args:
        server_borders (tuple): The borders of the server.
    """
    while True:
        data, addr = sock.recvfrom(4096)
        handle_packet(data, addr, server_borders)

def packet_info(data):
    """
    Extracts and decodes the packet information.
    
    Args:
        data: The raw packet data.
        
    Returns:
        dict: The decoded packet information.
    """
    try:
        return json.loads(data.decode())
    except:
        print("Error: Could not decode packet")
        return None 

def MoveServer(packet_info, server_borders) -> (dict, dict):
    """
    Determines the right server for each packet based on its coordinates.
    
    Args:
        packet_info (dict): The packet information.
        server_borders (tuple): The borders of the server.
        
    Returns:
        dict: A dictionary mapping packet IDs to server IDs.
    """
    right_servers = {}
    server_to_send = {}
    for id, properties in packet_info.items():
        if properties["x"] < server_borders[0] and properties["y"] < server_borders[1]:
            right_servers[id] = 1
        elif properties["x"] > server_borders[0] and properties["y"] > server_borders[1]:
            right_servers[id] = 3
        elif properties["x"] < server_borders[0] and properties["y"] > server_borders[1]:
            right_servers[id] = 4
        else:
            right_servers[id] = 2

        HandlePlayerServer(id, properties, server_to_send, right_servers)
        
    return right_servers, server_to_send

def HandlePlayerServer(id, properties, server_to_send, right_servers):
    if (server_borders[0] - MAX_ATTACK < properties['x'] < server_borders[0] + MAX_ATTACK):
        if (properties['y'] < server_borders[1] - MAX_ATTACK):
            server_to_send[id] = [1, 2]
        elif (properties['y'] > server_borders[1] + MAX_ATTACK):
            server_to_send[id] = [3, 4]
        else:
            server_to_send[id] = [1, 22, 3, 4]
    else:
        if (properties['x'] < server_borders[0] - MAX_ATTACK):
            server_to_send[id] = [1, 4]
        else:
            server_to_send[id] = [2, 3]
    
    server_to_send[id].remove(properties['server'])

def BuildPacket(packet_info, addr):
    """
    Builds a packet from the packet information.
    
    Args:
        packet_info (dict): The packet information.
        addr: The address of the original packet sender.
        
    Returns:
        bytes: The constructed packet as bytes.
    """
    response = {
        "dst": addr[0],
        "dport": addr[1],
        "data": packet_info
    }
    return json.dumps(response).encode()

def DictToString(dict) -> str:
    """
    Converts a dictionary to a JSON string.
    
    Args:
        dict (dict): The dictionary to convert.
        
    Returns:
        str: The JSON string representation of the dictionary.
    """
    return json.dumps(dict)

def handle_packet(data, addr, server_borders):
    """
    Handles incoming packets and processes them.
    
    Args:
        data: The incoming packet data.
        addr: The address of the packet sender.
        server_borders (tuple): The borders of the server.
    """
    packet_info = packet_info(data)
    if packet_info is None:
        return "Error: Could not decode packet"
    
    right_servers, server_to_send = MoveServer(packet_info, server_borders)
    response = BuildPacket(right_servers, addr)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(response, addr)
    return "Packet has been processed"

if __name__ == "__main__":

    main()
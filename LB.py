from scapy.all import *
from scapy.layers.inet import *
import json

# List of server IPs
SERVER_IPS = []
# List of server ports
SERVER_PORTS = []
# Load balancer port
LB_PORT = 1111111
LB_IP = '127.0.0.1'
# Map dimensions
MAP_WIDTH = 38400
MAP_HEIGHT = 34560
# Maximum attack range
MAX_ATTACK = 300

def main(server_borders):
    """
    Main function to start sniffing packets.
    
    Args:
        server_borders (tuple): The borders of the server.
    """
    sniff(prn=handle_packet, filter=f"udp port {LB_PORT}", store=0)

def packet_info(packet):
    """
    Extracts and decodes the packet information.
    
    Args:
        packet: The packet to extract information from.
        
    Returns:
        dict: The decoded packet information.
    """
    packet_Raw = packet[scapy.Raw].load.decode()
    try:
        return json.loads(packet_Raw)
    except:
        print("Error: Could not decode packet")
        return None 

def MoveServer(packet_info, server_borders) -> dict:
    """
    Determines the right server for each packet based on its coordinates.
    
    Args:
        packet_info (dict): The packet information.
        server_borders (tuple): The borders of the server.
        
    Returns:
        dict: A dictionary mapping packet IDs to server IDs.
    """
    right_servers = {}
    for id, properties in packet_info.items():
        if properties["x"] < server_borders[0] + MAX_ATTACK and properties["y"] < server_borders[1] + MAX_ATTACK:
            right_servers[id] = 1
        if properties["x"] > server_borders[0] - MAX_ATTACK and properties["y"] > server_borders[1] - MAX_ATTACK:
            right_servers[id] = 3
        if properties["x"] < server_borders[0] + MAX_ATTACK and properties["y"] > server_borders[1] - MAX_ATTACK:
            right_servers[id] = 4
        if properties["x"] > server_borders[0] - MAX_ATTACK and properties["y"] < server_borders[1] - MAX_ATTACK:
            right_servers[id] = 2
        
    return right_servers

def BuildPacket(packet_info, req_packet):
    """
    Builds an HTTP packet from the packet information.
    
    Args:
        packet_info (dict): The packet information.
        
    Returns:
        scapy.layers.inet.IP: The constructed HTTP packet.
    """
    return IP(dst=req_packet[IP].src) / UDP(dport=req_packet[UDP].sport, sport=req_packet[UDP].dport) / Raw(load=DictToString(packet_info))

def DictToString(dict) -> str:
    """
    Converts a dictionary to a JSON string.
    
    Args:
        dict (dict): The dictionary to convert.
        
    Returns:
        str: The JSON string representation of the dictionary.
    """
    return json.dumps(dict)

def handle_packet(packet):
    """
    Handles incoming packets and processes them.
    
    Args:
        packet: The incoming packet.
    """
    if packet.haslayer(UDP):
        if packet[UDP].dport == LB_PORT and packet[IP].src in SERVER_IPS and packet[IP].dst == LB_IP and packet.haslayer(Raw):
            if packet[UDP].sport not in SERVER_PORTS:
                return
            packet_info = packet_info(packet)
            right_servers = MoveServer(packet_info, server_borders)
            response = BuildPacket(right_servers, packet)
            send(response)



if __name__ == "__main__":
    server_borders = (MAP_WIDTH / 2, MAP_HEIGHT / 2)
    main(server_borders)
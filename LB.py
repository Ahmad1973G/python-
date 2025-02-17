from scapy.all import *

SERVER_PORTS = []
LB_PORT = 1111111

def main():
    sniff(prn=handle_packet, filter=f"udp port {LB_PORT}", store=0)

def packet_info(packet):
    packet_Raw = packet[scapy.Raw].load.decode()
    try:
        return json.loads(packet_Raw)
    except:
        print("Error: Could not decode packet")                       
        return None 

def MoveServer(packet_info, server_borders) -> dict:
    count = 1
    right_servers = {}
    while count * 5 <= len(packet_info):
        if (server_borders['server1'][0] >= packet_info['x' + count] and server_borders['server1'][1] >= packet_info['y' + count]):
            right_servers['server' + count] = 1
        if (server_borders['server2'][0] <= packet_info['x' + count] and server_borders['server1'][1] >= packet_info['y' + count]):
            right_servers['server' + count] = 2
        if (server_borders['server3'][0] <= packet_info['x' + count] and server_borders['server1'][1] <= packet_info['y' + count]):



def handle_packet(packet):
    if packet.haslayer(scapy.UDP):
        if packet[scapy.UDP].dport == LB_PORT:
            if packet[scapy.UDP].sport not in SERVER_PORTS:
                return
            server_borders = {'server1' : (1 , 1), 'server2' : (1, 1), 'server3' : (1, 1), 'server4' : (1, 1)}
            packet_info = packet_info(packet)

    
if __name__ == "__main__":
    main()
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
    if (packet_info['server' + count] == 1):
        if (server_borders['server' + count][0] >= packet_info['x' + count]):
            if (server_borders['server' + count])

        


def handle_packet(packet):
    if packet.haslayer(scapy.UDP):
        if packet[scapy.UDP].dport == LB_PORT:
            if packet[scapy.UDP].sport not in SERVER_PORTS:
                return
            server_borders = {'server1' : (1 , 1), 'server2' : (1, 1), 'server3' : (1, 1), 'server4' : (1, 1)}
            packet_info = packet_info(packet)

    
if __name__ == "__main__":
    main()
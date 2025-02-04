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

def handle_packet(packet):
    if packet.haslayer(scapy.UDP):
        if packet[scapy.UDP].dport == LB_PORT:
            if packet[scapy.UDP].sport not in SERVER_PORTS:
                return
    
    packet_info = packet_info(packet)

if __name__ == "__main__":
    main()
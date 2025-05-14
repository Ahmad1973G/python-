import socket
import threading
import random
import time

from scipy.spatial import KDTree
from typing import List

import sub_client_prots
import sub_lb_prots
import bots
import os
import pytmx

# Configuration
LB_PORT = 5002
UDP_PORT = LB_PORT + 1
SERVER_PORT = 5000

# Protocol Messages
SYN = "SYNC CODE 1"
SYN_ACK = "SYNC+ACK CODE 1"
ACK = "ACK CODE 2"


def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


def build_collision_kdtree(collidable_tiles):
    # Calculate center positions for KD-tree
    positions = [(x + w / 2, y - h / 2) for (x, w, y, h) in collidable_tiles]
    kd_tree = KDTree(positions)
    pos_to_tile = dict(zip(positions, collidable_tiles))
    return kd_tree, pos_to_tile


def get_collidable_tiles(tmx_data):
    """Returns a set of tile coordinates that are collidable."""
    collidable_tiles = set()
    for layer in tmx_data.layers:
        if isinstance(layer, pytmx.TiledObjectGroup):
            if layer.name == "no walk no shoot":
                for obj in layer:
                    # Add the coordinates of the collidable tile to the set
                    new_tile_tup = obj.x - 500, obj.width, obj.y - 330, obj.height
                    # collidable_tiles.add((obj.x // tmx_data.tilewidth, obj.y // tmx_data.tileheight))
                    collidable_tiles.add(new_tile_tup)
    return collidable_tiles


class SubServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind((get_ip_address(), UDP_PORT))
        self.server_address = (get_ip_address(), SERVER_PORT)
        self.server_socket.bind(self.server_address)
        self.server_socket.listen()
        self.server_socket.settimeout(5)
        self.load_balancer_address = (0, LB_PORT)
        self.connected_clients = {}
        self.is_connected_to_lb = False
        self.players_data = {}
        self.udp_socket.settimeout(4)
        self.server_id = 0
        self.server_index = 0
        self.server_borders = [0, 0]
        self.updated_elements = {}
        self.players_counter = {}
        self.players_to_lb = {}
        self.different_server_players = {}
        self.moving_servers = {}
        self.waiting_login = {}
        self.waiting_register = {}
        self.secret_players_data = {}
        self.players_cached = {}
        self.chat_logs = []
        self.sequence_id = 1
        self.bots = {}

        # Add locks for shared resources
        self.clients_lock = threading.Lock()
        self.players_data_lock = threading.Lock()
        self.elements_lock = threading.Lock()
        self.counter_lock = threading.Lock()
        self.lb_lock = threading.Lock()
        self.other_server_lock = threading.Lock()
        self.moving_lock = threading.Lock()
        self.waiting_login_lock = threading.Lock()
        self.waiting_register_lock = threading.Lock()
        self.secret_lock = threading.Lock()
        self.cache_lock = threading.Lock()
        self.logs_lock = threading.Lock()
        self.sequence_lock = threading.Lock()

        self.process_move = sub_client_prots.process_move
        self.process_shoot = sub_client_prots.process_shoot
        self.process_damage_taken = sub_client_prots.process_damage_taken
        self.process_power = sub_client_prots.process_power
        self.process_angle = sub_client_prots.process_angle
        self.process_request = sub_client_prots.process_request
        self.process_requestFull = sub_client_prots.process_requestFull
        self.process_login = sub_client_prots.process_login
        self.process_register = sub_client_prots.process_register
        self.process_Money = sub_client_prots.process_Money
        self.process_Ammo = sub_client_prots.process_Ammo
        self.process_Inventory = sub_client_prots.process_Inventory
        self.process_Bomb = sub_client_prots.process_boom
        self.process_chat_recv = sub_client_prots.process_chat_recv
        self.process_chat_send = sub_client_prots.process_chat_send
        self.process_chat = sub_client_prots.process_chat

        self.getINDEX = sub_lb_prots.getINDEX
        self.getRIGHT = sub_lb_prots.getRIGHT
        self.getBORDERS = sub_lb_prots.getBORDERS
        self.getSEND = sub_lb_prots.getSEND
        self.AddToLB = sub_lb_prots.AddToLB
        self.CheckForLB = sub_lb_prots.CheckForLB
        self.SendInfoLB = sub_lb_prots.SendInfoLB
        self.SendRegister = sub_lb_prots.SendRegister
        self.SendLogin = sub_lb_prots.SendLogin
        self.SendCache = sub_lb_prots.SendCache
        self.SortRegister = sub_lb_prots.SortRegister
        self.SortLogin = sub_lb_prots.SortLogin

        self.protocols = {
            "MOVE": self.process_move,
            "SHOOT": self.process_shoot,
            "DAMAGE": self.process_damage_taken,
            "POWER": self.process_power,
            "ANGLE": self.process_angle,
            "LOGIN": self.process_login,
            "REGISTER": self.process_register,
            "MONEY": self.process_Money,
            "AMMO": self.process_Ammo,
            "INVENTORY": self.process_Inventory,
            "BOMB": self.process_Bomb,
            "CHAT": self.process_chat,
        }

        self.receive_protocol = {
            "REQUEST": self.process_request,
            "REQUESTFULL": self.process_requestFull
        }

        script_dir = os.path.dirname(__file__)
        map_path = os.path.join(script_dir, "map", "map.tmx")

        tmx_data = pytmx.load_pygame(map_path)
        collidable_tiles = get_collidable_tiles(tmx_data)
        self.kd_tree, self.pos_to_tile = build_collision_kdtree(collidable_tiles)
        self.SetBots()

    def get_random_bot_position(self, borders):
        bot_x, bot_y = (random.randint(borders[0], borders[0] + self.server_borders[0]),
                        random.randint(borders[1], borders[1] + self.server_borders[1]))
        return bot_x, bot_y

    def SetBots(self):
        if self.server_index == 1:
            borders = (0, 0)
        elif self.server_index == 2:
            borders = (self.server_borders[0], 0)
        elif self.server_index == 3:
            borders = self.server_borders
        else:
            borders = (0, self.server_borders[1])

        positions: List[tuple] = []
        for i in range(100):
            bot_x, bot_y = self.get_random_bot_position(borders)
            while (bot_x, bot_y) in positions:
                bot_x, bot_y = self.get_random_bot_position(borders)
            positions.append((bot_x, bot_y))
            bot_type = random.randint(0, 1)
            if bot_type == 0:
                bot_type = True
            else:
                bot_type = False
            bot = bots.Bot(bot_x, bot_y, bot_type, 0 ,0, self.kd_tree, self.pos_to_tile)
            self.bots[i] = bot



    def AskForID(self, conn):
        try:
            conn.send("ID".encode())
            data = conn.recv(1024).decode()
            if data.startswith("ID CODE 69"):
                client_id = int(data.split(";")[-1])
                print("Received ID from client:", client_id)
                return client_id
            else:
                print("Failed to receive ID from client, error:", data)
                return -1
        except Exception as e:
            print(f"Error receiving ID from client: {e}")
            return -1

    def WelcomePlayers(self, players):
        while True:
            conn = None
            try:
                with self.clients_lock:
                    conn, addr = self.server_socket.accept()
                    client_id = self.AskForID(conn)

                if client_id == -1:
                    conn.close()
                    continue
                if client_id not in players:
                    continue
                with self.clients_lock:
                    self.connected_clients[client_id] = (addr, conn)
                client_thread = threading.Thread(target=self.handle_client, args=(client_id,))
                client_thread.start()
                print(f"Started thread for client {client_id} from another server")
                players.remove(client_id)
                if not players:
                    break

            except socket.timeout:
                print("No connection received within timeout period, trying again")

            except Exception as e:
                print(f"Error accepting connection from client: {e}")
                if conn is not None:
                    conn.close()



    def CheckIfMoving(self, client_id):
        with self.moving_lock:
            if client_id in self.moving_servers.keys():
                return True, self.moving_servers[client_id]
            else:
                return False, 0

    def CheckIfMovingFULL(self, client_id):
        with self.clients_lock:
            cond, ip = self.CheckIfMoving(client_id)
            if not cond:
                self.connected_clients[client_id][1].send("ACK".encode())
                return

            self.connected_clients[client_id][1].send(f"MOVING {ip}".encode())


    def lb_connect_protocol(self):
        print("Listening on UDP for load balancer on", get_ip_address())
        while not self.is_connected_to_lb:
            try:
                data, _ = self.udp_socket.recvfrom(1024)
                print("Received UDP packet: ", data.decode())
                if self.readSYNcLB(data):
                    self.sendSYNCACKLB()
                    if self.recvACKLB():
                        self.is_connected_to_lb = True
                        lb_thread = threading.Thread(target=self.handle_lb)
                        lb_thread.start()
                        break
            except socket.timeout:
                print("No UDP packet received within timeout period")
            except Exception as e:
                print(f"Error receiving UDP packet: {e}")
                self.lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def handle_lb(self):
        self.getINDEX(self)
        self.getBORDERS(self)
        while True:
            try:
                # self.SendInfoLB()
                # self.getRIGHT()
                # self.getSEND()
                self.SendRegister()
                self.SendLogin()
                self.SendCache()
            except socket.timeout:
                print("No data received from load balancer within timeout period")
            except Exception as e:
                print(f"Error receiving data from load balancer: {e}")
                self.is_connected_to_lb = False
                break

    def readSYNcLB(self, data):
        str_data = data.decode()
        if str_data.startswith(SYN):
            lb_ip, lb_port = str_data.split(" ")[-1].split(",")[0].split(";")[1], int(
                str_data.split(" ")[-1].split(",")[1].split(";")[1])
            if lb_port == LB_PORT:
                try:
                    self.load_balancer_address = (lb_ip, lb_port)
                    self.lb_socket.connect(self.load_balancer_address)
                    print("SYNC Success")
                    return True
                except Exception as e:
                    print(f"Error connecting to load balancer: {e}")
        return False

    def sendSYNCACKLB(self):
        self.lb_socket.send(SYN_ACK.encode())

    def recvACKLB(self):
        data = self.lb_socket.recv(1024).decode()
        if data.startswith(ACK):
            print("Received ACK")
            self.server_id = int(data.split(";")[-1])
            print("Server ID:", self.server_id)
            return True
        return False

    def recvSYNclient_sendSYNACK(self, data, addr):
        str_data = data.decode()
        if str_data == "SYNC CODE 69":
            self.udp_socket.sendto(f"SYNC+ACK CODE 69 {self.server_address[0]};{self.server_address[1]}".encode(), addr)
            return True
        return False

    def sendID(self):
        try:
            conn, addr = self.server_socket.accept()
            print("Accepted connection from client")
            client_id = random.randint(1, 1000)
            with self.clients_lock:
                while client_id in self.connected_clients.keys():
                    client_id = random.randint(100, 1000)
                self.connected_clients[client_id] = (addr, conn)

            with self.players_data_lock:
                self.players_data[client_id] = {}

            conn.send(f"ID CODE 69 {client_id}".encode())
            print("Sent ID to client")
            return client_id
        except Exception as e:
            print(f"Error accepting connection from client: {e}")

    def client_start_protocol(self):
        print("Listening for clients")
        try:
            data, addr = self.udp_socket.recvfrom(1024)
            if self.recvSYNclient_sendSYNACK(data, addr):
                print("Received the SYNC packet successfully")
                print("Sent the SYNC+ACK packet")
                return self.sendID()
            return -1
        except socket.timeout:
            return -1
        except Exception as e:
            print(f"Error receiving UDP packet: {e}")
            return -1

    def client_connect_protocol(self):
        print("Listening for clients on", self.server_address)
        while self.is_connected_to_lb:
            client_id = self.client_start_protocol()
            if client_id == -1:
                continue
            print(f"Client connected.")
            client_thread = threading.Thread(target=self.handle_client, args=(client_id,))
            client_thread.start()
            print(f"Started thread for client {client_id}")
            print("Connected clients:", self.connected_clients.keys())
        print("Not listening to clients anymore.")

    def handle_client(self, client_id):
        with self.clients_lock:
            conn = self.connected_clients[client_id][1]
            client_address = self.connected_clients[client_id][0]

        with self.counter_lock:
            self.players_counter[client_id] = 0

        with self.elements_lock:
            self.updated_elements[client_id] = {}

        with self.players_data_lock:
            self.players_data[client_id] = {}

        print(f"Connected to client {client_id} at {client_address}")
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                message = data.decode()
                exit_cond = self.process_player_data(client_id, message)
                if exit_cond == 1:
                    break
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            print(f"Client {client_address} disconnected.")
            if client_id in self.players_cached and client_id in self.secret_players_data:
                with self.cache_lock and self.secret_lock:
                    self.players_cached[client_id] = self.secret_players_data[client_id]
                    del self.secret_players_data[client_id]
            with self.clients_lock:
                if client_id in self.connected_clients:
                    del self.connected_clients[client_id]

            with self.players_data_lock:
                if client_id in self.players_data:
                    del self.players_data[client_id]

            with self.counter_lock:
                if client_id in self.players_counter:
                    del self.players_counter[client_id]

            with self.elements_lock:
                self.updated_elements[client_id] = {'disconect': True}
                start_time = time.time()
                while True:
                    if time.time() - start_time > 10:
                        del self.updated_elements[client_id]
                        break
            conn.close()

    def process_player_data(self, client_id, message: str):
        try:
            messages = message.split(' ', maxsplit=1)
            protocol = messages[0]
            data = messages[-1]
            if protocol in self.protocols.keys():
                self.protocols[protocol](self, client_id, data)

            elif protocol in self.receive_protocol.keys():
                with self.elements_lock:
                    self.updated_elements[client_id] = {}
                return self.receive_protocol[protocol](self, client_id)

            else:
                print("Unknown protocol, ignoring")

            with self.counter_lock:
                self.players_counter[client_id] = 0

            return 0
        except Exception as e:
            print(f"Error processing player data for {client_id}: {e}")

    def run(self):
        lb_thread = threading.Thread(target=self.lb_connect_protocol)
        lb_thread.start()
        lb_thread.join()

        if self.is_connected_to_lb:
            self.client_connect_protocol()
        else:
            print("Load balancer not properly connected, not listening to clients.")


if __name__ == "__main__":
    server = SubServer()
    server.run()
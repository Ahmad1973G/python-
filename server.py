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
import players_grid
# Configuration
LB_PORT = 5002
UDP_PORT = LB_PORT + 1
SERVER_PORT = 5000

# Protocol Messages
SYN = "SYNC CODE 1"
SYN_ACK = "SYNC+ACK CODE 1"
ACK = "ACK CODE 2"

RADIUS = 600

def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


def get_collidable_tiles_optimized(tmx_data):
    """Optimized version of collision tile processing"""
    collidable_tiles = set()
    for layer in tmx_data.layers:
        if isinstance(layer, pytmx.TiledObjectGroup) and layer.name == "no walk no shoot":
            # Process all objects in batch
            collidable_tiles.update(
                (obj.x - 500, obj.width, obj.y - 330, obj.height)
                for obj in layer
            )
    return collidable_tiles


def build_collision_kdtree_optimized(collidable_tiles):
    """Optimized version of KD-tree building"""
    # Pre-calculate all positions in one go
    positions = [(x + w / 2, y - h / 2) for (x, w, y, h) in collidable_tiles]

    # Build KD-tree with faster algorithm
    kd_tree = KDTree(positions, leafsize=16)  # Increased leaf size for better performance

    # Create position mapping using dict comprehension
    pos_to_tile = {pos: tile for pos, tile in zip(positions, collidable_tiles)}

    return kd_tree, pos_to_tile


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
        self.bots_lock = threading.Lock()
        self.grid_lock = threading.Lock()

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
        self.process_bot_damage = sub_client_prots.process_bot_damage

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
            "HEALTH": self.process_damage_taken,
            "POWER": self.process_power,
            "ANGLE": self.process_angle,
            "LOGIN": self.process_login,
            "REGISTER": self.process_register,
            "MONEY": self.process_Money,
            "AMMO": self.process_Ammo,
            "INVENTORY": self.process_Inventory,
            "BOMB": self.process_Bomb,
            "CHAT": self.process_chat,
            "DAMAGE": self.process_bot_damage,
        }

        self.receive_protocol = {
            "REQUEST": self.process_request,
            "REQUESTFULL": self.process_requestFull
        }

        script_dir = os.path.dirname(__file__)
        map_path = os.path.join(script_dir, "map", "map.tmx")

        tmx_data = pytmx.TiledMap(map_path, load_all_tiles=False)
        print("Loaded map data successfully")
        collidable_tiles = get_collidable_tiles_optimized(tmx_data)
        print("Extracted collidable tiles successfully")
        self.kd_tree, self.pos_to_tile = build_collision_kdtree_optimized(collidable_tiles)
        print("Built KD-tree successfully")

        # Initialize the grid
        self.grid = players_grid.PlayersGrid(cell_size=1000)

    def restart_bot(self, bot_id):
        time.sleep(1)
        borders = {
            1: (0, 0),
            2: (self.server_borders[0], 0),
            3: self.server_borders,
            4: (0, self.server_borders[1])
        }.get(self.server_index, (0, 0))
        new_x, new_y = self.get_random_bot_position(borders)
        with self.grid_lock:
            nearby = self.grid.get_nearby_players(new_x, new_y, 100)
            while len(nearby) > 0:
                new_x, new_y = self.get_random_bot_position(borders)
                nearby = self.grid.get_nearby_players(new_x, new_y, 100)
        with self.bots_lock:
            self.bots[bot_id].my_x = new_x
            self.bots[bot_id].my_y = new_y
            self.bots[bot_id].closest_x = None
            self.bots[bot_id].closest_y = None
        with self.elements_lock:
            self.updated_elements[bot_id]['x'] = new_x
            self.updated_elements[bot_id]['y'] = new_y
        with self.players_data_lock:
            self.players_data[bot_id]['x'] = new_x
            self.players_data[bot_id]['y'] = new_y
        with self.grid_lock:
            self.grid.add_player(bot_id, new_x, new_y)


    def get_random_bot_position(self, borders):
        bot_x, bot_y = (random.randint(borders[0], borders[0] + self.server_borders[0]),
                        random.randint(borders[1], borders[1] + self.server_borders[1]))
        return bot_x, bot_y

    def SetBots(self, amount):
        borders = {
            1: (0, 0),
            2: (self.server_borders[0], 0),
            3: self.server_borders,
            4: (0, self.server_borders[1])
        }.get(self.server_index, (0, 0))

        # Generate more positions than needed to avoid too many collisions
        all_positions = set()
        while len(all_positions) < amount:
            x = borders[0] + random.randint(0, self.server_borders[0])
            y = borders[1] + random.randint(0, self.server_borders[1])
            all_positions.add((x, y))
        print("Generated positions for bots:", all_positions)
        # Create bots in batch
        positions = list(all_positions)[:amount]  # Take first x positions
        bot_types = [random.random() < 0.5 for _ in range(amount)]  # Pre-generate all bot types

        # Create bots and update data structures in batch
        for i, ((x, y), is_type_0) in enumerate(zip(positions, bot_types)):
            bot = bots.Bot(x, y, is_type_0, 0, 0, self.kd_tree, self.pos_to_tile)

            # Update both dictionaries at once under a single lock
            with self.players_data_lock:
                self.players_data[i] = {
                    'x': x,
                    'y': y,
                    'type': is_type_0,
                    'angle': 0,
                    'health': 100
                }
            with self.elements_lock:
                self.updated_elements[i] = {}
            with self.bots_lock:
                self.bots[i] = bot
            with self.grid_lock:
                self.grid.add_player(i, x, y)

    def CheckForBots(self, x, y):
        with self.bots_lock:
            for bot_id, bot in self.bots.items():
                if abs(bot.my_x - x) < RADIUS and abs(bot.my_y - y) < RADIUS:
                    bot.SeNdTArGeT(x, y)
                    print(f"Bot {bot_id} is moving towards ({x}, {y})")

    def MovingBots(self):
        with self.bots_lock:
            bots_copy = self.bots.copy()

        for bot_id, bot in bots_copy.items():
            if bot.moving:
                print(f"Bot {bot_id} is moving")
                with self.players_data_lock:
                    self.players_data[bot_id]['x'] = bot.my_x
                    self.players_data[bot_id]['y'] = bot.my_y

                with self.elements_lock:
                    self.updated_elements[bot_id]['x'] = bot.my_x
                    self.updated_elements[bot_id]['y'] = bot.my_y
                    print(f"Bot {bot_id} position updated to ({bot.my_x}, {bot.my_y})")

                with self.grid_lock:
                    self.grid.add_player(bot_id, bot.my_x, bot.my_y)
            else:
                with self.elements_lock:
                    if bot_id in self.updated_elements:
                        if 'x' in self.updated_elements[bot_id]:
                            del self.updated_elements[bot_id]['x']
                            del self.updated_elements[bot_id]['y']

    def ShootingBots(self):
        with self.bots_lock:
            bots_copy = self.bots.copy()
        
        for bot_id, bot in bots_copy.items():
            if bot.shooting:
                with self.elements_lock:
                    self.updated_elements[bot_id]['shoot'] = [bot.my_x, bot.my_y, bot.closest_x, bot.closest_y]
            else:
                with self.elements_lock:
                    if bot_id in self.updated_elements:
                        if 'shoot' in self.updated_elements[bot_id]:
                            del self.updated_elements[bot_id]['shoot']
    
    def BotManage(self):
        print("Bot management started")
        while True:
            self.MovingBots()
            self.ShootingBots()
            time.sleep(1)  # Adjust the sleep time as needed

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
                with self.players_data_lock:
                    self.players_data[client_id] = {}
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
        self.SetBots(25)
        while True:
            try:
                # self.SendInfoLB()
                # self.getRIGHT()
                # self.getSEND()
                self.SendRegister(self)
                self.SendLogin(self)
                self.SendCache(self)
            except socket.timeout:
                print("No data received from load balancer within timeout period")
            except Exception as e:
                print(f"Error receiving data from load balancer: {e}")
                self.is_connected_to_lb = False
                break


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
            client_id = random.randint(100, 1000)
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

            with self.grid_lock:
                if client_id in self.grid.player_positions:
                    self.grid.remove_player(client_id)

            with self.elements_lock:
                self.updated_elements[client_id] = {'disconnect': True}
            start_time = time.time()
            while True:
                if time.time() - start_time > 10:
                    with self.elements_lock:
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

    def create_new_pos(self):
        borders = {
            1: (0, 0),
            2: (self.server_borders[0], 0),
            3: self.server_borders,
            4: (0, self.server_borders[1])
        }.get(self.server_index, (0, 0))
                
        x, y = self.get_random_bot_position(borders)
        while True:
            with self.grid_lock:
                nearby = self.grid.get_nearby_players(x, y, 100)
                if len(nearby) == 0:
                    break
                else:
                    x, y = self.get_random_bot_position(borders)
        return x, y

    def run(self):
        lb_thread = threading.Thread(target=self.lb_connect_protocol)
        lb_thread.start()
        lb_thread.join()

        if self.is_connected_to_lb:
            clients_thread = threading.Thread(target=self.client_connect_protocol)
            clients_thread.start()

            bots_thread = threading.Thread(target=self.BotManage)
            bots_thread.start()
        else:
            print("Load balancer not properly connected, not listening to clients.")


    


if __name__ == "__main__":
    server = SubServer()
    server.run()
import asyncio
import socket  # Still needed for gethostname, gethostbyname, SOL_SOCKET, SO_BROADCAST, AF_INET, SOCK_DGRAM
import random
import os
import json  # Added for process_request and process_requestFull, though it was implicitly used via sub_client_prots

from scipy.spatial import KDTree
from typing import List, Dict, Any, Tuple, Optional  # Added for type hints

import pytmx
import players_grid

# Assuming these will also be converted or are compatible
import sub_client_prots_async as sub_client_prots  # Renamed for clarity
import sub_lb_prots_async as sub_lb_prots  # Renamed for clarity
import bots

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
            collidable_tiles.update(
                (obj.x - 500, obj.width, obj.y - 330, obj.height)
                for obj in layer
            )
    return collidable_tiles


def build_collision_kdtree_optimized(collidable_tiles):
    """Optimized version of KD-tree building"""
    positions = [(x + w / 2, y - h / 2) for (x, w, y, h) in collidable_tiles]
    if not positions:  # KDTree fails with empty data
        return None, {}
    kd_tree = KDTree(positions, leafsize=16)
    pos_to_tile = {pos: tile for pos, tile in zip(positions, collidable_tiles)}
    return kd_tree, pos_to_tile


class ServerUDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, server_instance):
        self.server = server_instance
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        # Allow broadcasting if this protocol instance is also used for sending broadcasts
        sock = self.transport.get_extra_info('socket')
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def datagram_received(self, data, addr):
        # print(f"UDP datagram received from {addr}: {data.decode()}")
        asyncio.create_task(self.server.handle_udp_datagram(data, addr))

    def error_received(self, exc):
        print(f"UDP Error received: {exc}")

    def connection_lost(self, exc):
        print(f"UDP Connection lost: {exc}")


class SubServer:
    def __init__(self):
        self.server_address = (get_ip_address(), SERVER_PORT)
        self.load_balancer_address = ('', LB_PORT)  # IP will be discovered

        self.lb_reader: Optional[asyncio.StreamReader] = None
        self.lb_writer: Optional[asyncio.StreamWriter] = None

        self.udp_transport: Optional[asyncio.DatagramTransport] = None
        self.udp_protocol: Optional[ServerUDPProtocol] = None

        self.connected_clients: Dict[int, Tuple[Any, asyncio.StreamReader, asyncio.StreamWriter]] = {}
        self.is_connected_to_lb = False
        self.players_data = {}
        self.server_id = 0
        self.server_index = 0
        self.server_borders = [0.0, 0.0]  # Ensure float for potential division
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

        # Assign async protocol methods
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
            "MOVE": self.process_move, "SHOOT": self.process_shoot,
            "HEALTH": self.process_damage_taken, "POWER": self.process_power,
            "ANGLE": self.process_angle, "LOGIN": self.process_login,
            "REGISTER": self.process_register, "MONEY": self.process_Money,
            "AMMO": self.process_Ammo, "INVENTORY": self.process_Inventory,
            "BOMB": self.process_Bomb, "CHAT": self.process_chat,
            "DAMAGE": self.process_bot_damage,
        }
        self.receive_protocol = {
            "REQUEST": self.process_request, "REQUESTFULL": self.process_requestFull
        }

        script_dir = os.path.dirname(__file__)
        map_path = os.path.join(script_dir, "map", "map.tmx")
        tmx_data = pytmx.TiledMap(map_path, load_all_tiles=False)
        print("Loaded map data successfully")
        collidable_tiles = get_collidable_tiles_optimized(tmx_data)
        print("Extracted collidable tiles successfully")
        self.kd_tree, self.pos_to_tile = build_collision_kdtree_optimized(collidable_tiles)
        if self.kd_tree:
            print("Built KD-tree successfully")
        else:
            print("KD-tree is empty or failed to build.")

        self.grid = players_grid.PlayersGrid(cell_size=1000)

        self._lb_syn_received_event = asyncio.Event()
        self._client_syn_received_event = asyncio.Event()
        self._pending_client_syn_addr = None

    async def async_init(self):
        # Create all asyncio primitives here, inside the running event loop
        self.clients_lock = asyncio.Lock()
        self.players_data_lock = asyncio.Lock()
        self.elements_lock = asyncio.Lock()
        self.counter_lock = asyncio.Lock()
        self.lb_lock = asyncio.Lock()
        self.other_server_lock = asyncio.Lock()
        self.moving_lock = asyncio.Lock()
        self.waiting_login_lock = asyncio.Lock()
        self.waiting_register_lock = asyncio.Lock()
        self.secret_lock = asyncio.Lock()
        self.cache_lock = asyncio.Lock()
        self.logs_lock = asyncio.Lock()
        self.sequence_lock = asyncio.Lock()
        self.bots_lock = asyncio.Lock()
        self.grid_lock = asyncio.Lock()
        self._lb_syn_received_event = asyncio.Event()
        self._client_syn_received_event = asyncio.Event()

    async def setup_udp_listener(self):
        loop = asyncio.get_running_loop()
        self.udp_transport, self.udp_protocol = await loop.create_datagram_endpoint(
            lambda: ServerUDPProtocol(self),
            local_addr=(get_ip_address(), UDP_PORT),
            # allow_broadcast=True # Already set in protocol's connection_made
        )
        print(f"UDP Listener started on {get_ip_address()}:{UDP_PORT}")

    async def handle_udp_datagram(self, data: bytes, addr: Tuple[str, int]):
        message = data.decode()
        #print(f"Handling UDP from {addr}: {message}")
        if message.startswith(SYN) and self.is_connected_to_lb is False:  # From Load Balancer
            if await self.readSYNcLB(data, addr[0]):  # Pass IP from addr
                self._lb_syn_received_event.set()
        elif message == "SYNC CODE 69":  # From Client
            self._pending_client_syn_addr = addr
            self._client_syn_received_event.set()

    async def restart_bot(self, bot_id):
        await asyncio.sleep(1)  # Non-blocking sleep
        borders = {
            1: (0, 0),
            2: (self.server_borders[0], 0),
            3: (self.server_borders[0], self.server_borders[1]),  # Corrected from self.server_borders
            4: (0, self.server_borders[1])
        }.get(self.server_index, (0, 0))

        new_x, new_y = self.get_random_bot_position(borders)
        async with self.grid_lock:
            # Ensure players_data is accessed safely if needed by get_nearby_players
            async with self.players_data_lock:
                nearby = self.grid.get_nearby_players(new_x, new_y,
                                                      100)  # Assuming this method is thread/async-safe or accesses data via locks
            while len(nearby) > 0:
                new_x, new_y = self.get_random_bot_position(borders)
                async with self.players_data_lock:
                    nearby = self.grid.get_nearby_players(new_x, new_y, 100)

        async with self.bots_lock:
            if bot_id in self.bots:
                self.bots[bot_id].my_x = new_x
                self.bots[bot_id].my_y = new_y
                self.bots[bot_id].closest_x = None
                self.bots[bot_id].closest_y = None
                self.bots[bot_id].health = 150  # Reset health
        async with self.elements_lock:
            if bot_id not in self.updated_elements: self.updated_elements[bot_id] = {}
            self.updated_elements[bot_id]['x'] = new_x
            self.updated_elements[bot_id]['y'] = new_y
            self.updated_elements[bot_id]['health'] = 100
        async with self.players_data_lock:
            if bot_id not in self.players_data: self.players_data[bot_id] = {}
            self.players_data[bot_id]['x'] = new_x
            self.players_data[bot_id]['y'] = new_y
            self.players_data[bot_id]['health'] = 150
        async with self.grid_lock:
            self.grid.add_player(bot_id, new_x, new_y)  # Assuming grid methods are safe

    def get_random_bot_position(self, borders):
        # Ensure server_borders elements are numbers
        border_x_end = borders[0] + (self.server_borders[0] if self.server_borders[0] is not None else 0)
        border_y_end = borders[1] + (self.server_borders[1] if self.server_borders[1] is not None else 0)

        bot_x = random.randint(int(borders[0]), int(border_x_end))
        bot_y = random.randint(int(borders[1]), int(border_y_end))
        return bot_x, bot_y

    async def SetBots(self, amount):
        borders = {
            1: (0, 0),
            2: (self.server_borders[0], 0),
            3: (self.server_borders[0], self.server_borders[1]),
            4: (0, self.server_borders[1])
        }.get(self.server_index, (0, 0))

        all_positions = set()
        # Check if server_borders are valid before using them
        if self.server_borders[0] is None or self.server_borders[1] is None or self.server_borders[0] == 0 or \
                self.server_borders[1] == 0:
            print(
                f"Warning: Server borders are not properly set ({self.server_borders}), cannot generate bot positions effectively.")
            # Fallback or constrained random positions if borders are problematic
            max_x_offset = 1000 if self.server_borders[0] is None or self.server_borders[0] == 0 else \
            self.server_borders[0]
            max_y_offset = 1000 if self.server_borders[1] is None or self.server_borders[1] == 0 else \
            self.server_borders[1]
        else:
            max_x_offset = self.server_borders[0]
            max_y_offset = self.server_borders[1]

        while len(all_positions) < amount:
            x = borders[0] + random.randint(0, int(max_x_offset))
            y = borders[1] + random.randint(0, int(max_y_offset))
            all_positions.add((x, y))

        positions = list(all_positions)[:amount]
        bot_types = [random.random() < 0.5 for _ in range(amount)]

        for i, ((x, y), is_type_0) in enumerate(zip(positions, bot_types)):
            bot = bots.Bot(x, y, is_type_0, 0, 0, self.kd_tree, self.pos_to_tile)
            async with self.players_data_lock:
                self.players_data[i] = {'x': x, 'y': y, 'type': is_type_0, 'angle': 0, 'health': 100}
            async with self.elements_lock:
                self.updated_elements[i] = {}
            async with self.bots_lock:
                self.bots[i] = bot
            async with self.grid_lock:
                self.grid.add_player(i, x, y)
        print(f"Set up {len(self.bots)} bots.")

    async def CheckForBots(self, x, y):
        async with self.bots_lock:
            # Create a copy for safe iteration if Bot.SeNdTArGeT modifies the collection (it shouldn't)
            bots_to_check = list(self.bots.items())

        for bot_id, bot in bots_to_check:
            if abs(bot.my_x - x) < RADIUS and abs(bot.my_y - y) < RADIUS:
                if hasattr(bot, 'SeNdTArGeT') and callable(bot.SeNdTArGeT):  # Check if method exists
                    # Assuming SeNdTArGeT can be async or is quick
                    if asyncio.iscoroutinefunction(bot.SeNdTArGeT):
                        await bot.SeNdTArGeT(x, y)
                    else:
                        bot.SeNdTArGeT(x, y)  # If it's synchronous
                    # print(f"Bot {bot_id} is moving towards ({x}, {y})")
                else:
                    print(f"Warning: Bot {bot_id} does not have SeNdTArGeT method.")

    async def MovingBots(self):
        active_bots = []
        async with self.bots_lock:
            # Iterate over a copy of items if bot.moving can lead to modification of self.bots
            bots_copy = list(self.bots.items())

        for bot_id, bot in bots_copy:
            if bot.moving:  # Assuming bot.moving and position updates are handled within bot object's logic
                # Bot internal state update might happen in its own async task or a synchronous method
                # For this conversion, we assume bot.update_position() or similar is called by bot's logic
                # Here, we just read the updated positions.

                # Call bot's update method if it's async
                if hasattr(bot, 'update') and asyncio.iscoroutinefunction(bot.update):
                    await bot.update()
                elif hasattr(bot, 'update'):  # Or sync
                    bot.update()

                async with self.players_data_lock:
                    self.players_data[bot_id]['x'] = bot.my_x
                    self.players_data[bot_id]['y'] = bot.my_y
                async with self.elements_lock:
                    self.updated_elements[bot_id]['x'] = bot.my_x
                    self.updated_elements[bot_id]['y'] = bot.my_y
                async with self.grid_lock:
                    self.grid.add_player(bot_id, bot.my_x, bot.my_y)
            else:  # Not moving
                async with self.elements_lock:
                    if bot_id in self.updated_elements:
                        if 'x' in self.updated_elements[bot_id]:
                            del self.updated_elements[bot_id]['x']
                        if 'y' in self.updated_elements[bot_id]:  # Check for y separately
                            del self.updated_elements[bot_id]['y']

    async def ShootingBots(self):
        async with self.bots_lock:
            bots_copy = list(self.bots.items())

        for bot_id, bot in bots_copy:
            if bot.shooting:  # Assuming bot.shooting is set by bot's internal logic
                async with self.elements_lock:
                    self.updated_elements[bot_id]['shoot'] = [bot.my_x, bot.my_y, bot.closest_x, bot.closest_y]
            else:
                async with self.elements_lock:
                    if bot_id in self.updated_elements and 'shoot' in self.updated_elements[bot_id]:
                        del self.updated_elements[bot_id]['shoot']

    async def BotManage(self):
        print("Bot management started")
        while True:
            await self.MovingBots()
            await self.ShootingBots()
            await asyncio.sleep(0.1)  # More frequent updates for bots

    async def AskForID(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            writer.write("ID".encode())
            await writer.drain()
            data = await reader.read(1024)
            message = data.decode()
            if message.startswith("ID CODE 69"):
                client_id = int(message.split(";")[-1])
                print("Received ID from client:", client_id)
                return client_id
            else:
                print("Failed to receive ID from client, error:", message)
                return -1
        except Exception as e:
            print(f"Error receiving ID from client: {e}")
            return -1

    async def WelcomePlayers(self, players_to_welcome: List[int], server_socket_for_welcome: asyncio.AbstractServer):
        # This method needs to accept connections on the main server socket temporarily for these specific clients
        # This is tricky because the main accept loop is separate.
        # A better approach might be for these clients to try reconnecting with their ID.
        # For now, let's assume the main server accept loop can delegate.
        # This implementation is simplified and might need adjustment based on how `server_socket_for_welcome` works.
        # It's better if the client initiates a new connection and sends its ID immediately.
        # The current `WelcomePlayers` in `server.py` uses `self.server_socket.accept()`.
        # The `asyncio.start_server` callback handles new connections.
        # A list of expected IDs could be checked there.
        # This method seems designed for a blocking accept specific to these players.
        # This will be redesigned to fit asyncio's model: the main `handle_new_connection` will check this list.
        print(
            f"WelcomePlayers logic needs to be integrated into the main connection handler for specific IDs: {players_to_welcome}")
        # For now, this function won't actively accept, but rely on handle_new_connection logic
        # that will check if an incoming ID (after handshake) is in a "welcome list".
        async with self.moving_lock:  # Assuming moving_servers holds IPs for redirection, which implies these are *new* connections after redirection
            pass  # Logic shifts to handle_new_connection

    async def CheckIfMoving(self, client_id):
        async with self.moving_lock:
            if client_id in self.moving_servers:
                return True, self.moving_servers[client_id]
            else:
                return False, 0

    async def CheckIfMovingFULL(self, client_id, writer: asyncio.StreamWriter):
        async with self.clients_lock:  # Protect access to connected_clients and moving_servers
            cond, ip = await self.CheckIfMoving(client_id)
            if not cond:
                writer.write("ACK".encode())
                await writer.drain()
                return

            writer.write(f"MOVING {ip}".encode())  # IP should be the new server's IP for client to connect
            await writer.drain()

    async def lb_connect_protocol(self):
        print("Listening on UDP for load balancer on", get_ip_address())
        while not self.is_connected_to_lb:
            try:
                await asyncio.wait_for(self._lb_syn_received_event.wait(), timeout=4.0)
                self._lb_syn_received_event.clear()  # Reset for next potential attempt
                # SYNC was received and processed by readSYNcLB via handle_udp_datagram

                await self.sendSYNCACKLB()
                if await self.recvACKLB():
                    self.is_connected_to_lb = True
                    print("Successfully connected to Load Balancer.")
                    asyncio.create_task(self.handle_lb())
                    break
                else:
                    # Close connection if ACK failed, so readSYNcLB can retry connect
                    if self.lb_writer:
                        self.lb_writer.close()
                        await self.lb_writer.wait_closed()
                    self.lb_reader = None
                    self.lb_writer = None

            except asyncio.TimeoutError:
                print("No UDP packet from LB received within timeout period. Retrying broadcast listen.")
            except ConnectionRefusedError:
                print("LB connection refused. Retrying...")
                await asyncio.sleep(1)  # Wait before retrying
            except Exception as e:
                print(f"Error in lb_connect_protocol: {e}")
                if self.lb_writer:
                    self.lb_writer.close()
                    # await self.lb_writer.wait_closed() # Not always available/needed depending on state
                self.lb_reader, self.lb_writer = None, None
                await asyncio.sleep(1)  # Wait before retrying

    async def handle_lb(self):
        await self.getINDEX(self)
        await self.getBORDERS(self)
        await self.SetBots(25)  # Make sure SetBots is async
        while self.is_connected_to_lb:
            try:
                if not self.lb_reader or not self.lb_writer or self.lb_reader.at_eof():
                    print("LB connection lost. Attempting to reconnect.")
                    self.is_connected_to_lb = False  # Trigger re-connection
                    asyncio.create_task(self.lb_connect_protocol())  # Restart connection process
                    return

                # await self.SendInfoLB(self) # Uncomment if needed
                # await self.getRIGHT(self)   # Uncomment if needed
                # await self.getSEND(self)    # Uncomment if needed
                await self.SendRegister(self)
                await self.SendLogin(self)
                await self.SendCache(self)
                await asyncio.sleep(0.1)  # Main loop delay for LB communication
            except ConnectionResetError:
                print("Connection to LB reset by peer.")
                self.is_connected_to_lb = False
                if self.lb_writer: self.lb_writer.close()
                asyncio.create_task(self.lb_connect_protocol())
                break
            except Exception as e:
                print(f"Error in handle_lb: {e}")
                self.is_connected_to_lb = False
                if self.lb_writer: self.lb_writer.close()
                # Consider await self.lb_writer.wait_closed() if applicable
                asyncio.create_task(self.lb_connect_protocol())  # Restart connection process
                break

    async def readSYNcLB(self, data_bytes, lb_ip_from_udp):  # lb_ip passed from UDP handler
        str_data = data_bytes.decode()
        if str_data.startswith(SYN):
            # UDP SYN "SYNC CODE 1, IP;{IP},PORT;{PORT}"
            parts = str_data.split(" ")[-1].split(",")
            lb_ip = parts[0].split(";")[1]
            lb_port_from_msg = int(parts[1].split(";")[1])

            # Verify if the received lb_ip matches the source IP of the UDP packet for security/consistency
            if lb_ip != lb_ip_from_udp:
                print(
                    f"Warning: LB SYN IP ({lb_ip}) differs from UDP source IP ({lb_ip_from_udp}). Using UDP source IP.")
                # This could be a configuration issue or an attempt to spoof.
                # Depending on security requirements, you might reject or log this.
                # For now, we'll trust the UDP source IP for the TCP connection.

            if lb_port_from_msg == LB_PORT:
                try:
                    print(f"Attempting to connect to LB at {lb_ip_from_udp}:{lb_port_from_msg}")
                    self.lb_reader, self.lb_writer = await asyncio.open_connection(lb_ip_from_udp, lb_port_from_msg)
                    self.load_balancer_address = (lb_ip_from_udp, lb_port_from_msg)
                    print("TCP SYNC with LB: Connection established.")
                    return True
                except ConnectionRefusedError:
                    print(f"TCP SYNC with LB: Connection refused by {lb_ip_from_udp}:{lb_port_from_msg}.")
                except Exception as e:
                    print(f"Error connecting to load balancer via TCP: {e}")
        return False

    async def sendSYNCACKLB(self):
        if self.lb_writer:
            self.lb_writer.write(SYN_ACK.encode())
            await self.lb_writer.drain()
            print("Sent SYNC+ACK to LB")

    async def recvACKLB(self):
        if self.lb_reader:
            try:
                data = await asyncio.wait_for(self.lb_reader.read(1024), timeout=5.0)
                message = data.decode()
                if message.startswith(ACK):
                    print("Received ACK from LB")
                    self.server_id = int(message.split(";")[-1])
                    print("Server ID:", self.server_id)
                    return True
                else:
                    print(f"LB ACK reception failed or malformed: {message}")
            except asyncio.TimeoutError:
                print("Timeout receiving ACK from LB.")
            except Exception as e:
                print(f"Error receiving ACK from LB: {e}")
        return False

    async def recvSYNclient_sendSYNACK(self, addr):  # addr is from UDP
        if self.udp_transport:
            # Send SYN+ACK back to client via UDP
            message = f"SYNC+ACK CODE 69 {self.server_address[0]};{self.server_address[1]}".encode()
            self.udp_transport.sendto(message, addr)
            print(f"Sent UDP SYNC+ACK to client {addr}")
            return True
        return False

    async def sendID_to_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_addr):
        client_id = random.randint(1000, 9999)  # Larger range for IDs
        async with self.clients_lock:
            while client_id in self.connected_clients:  # Ensure unique ID
                client_id = random.randint(1000, 9999)
            # Store reader/writer pair for the client
            self.connected_clients[client_id] = (client_addr, reader, writer)

        async with self.players_data_lock:  # Initialize player data structure
            self.players_data[client_id] = {}  # Basic init

        writer.write(f"ID CODE 69 {client_id}".encode())
        await writer.drain()
        print(f"Sent ID {client_id} to client {client_addr}")
        return client_id

    async def client_start_protocol(self):
        # This method now waits for a UDP SYN event triggered by ServerUDPProtocol
        print(f"Listening for client UDP SYNC on {get_ip_address()}:{UDP_PORT}")
        try:
            await asyncio.wait_for(self._client_syn_received_event.wait(),
                                   timeout=None)  # Wait indefinitely or with a timeout
            self._client_syn_received_event.clear()

            client_udp_addr = self._pending_client_syn_addr
            self._pending_client_syn_addr = None

            if client_udp_addr:
                if await self.recvSYNclient_sendSYNACK(client_udp_addr):  # Sends UDP SYN+ACK
                    print("Client SYNC received, UDP SYN+ACK sent. Client should now connect via TCP.")
                    # The actual TCP connection and ID sending will be handled by handle_new_connection
                    return True  # Signal that a client is expected
            return False
        except asyncio.TimeoutError:
            # print("Timeout waiting for client UDP SYNC.") # If timeout is used
            return False
        except Exception as e:
            print(f"Error in client_start_protocol (UDP phase): {e}")
            return False

    async def client_connect_listener_task(self, server: asyncio.AbstractServer):
        print(f"TCP Client Listener started on {self.server_address}. Waiting for client_start_protocol trigger.")
        while self.is_connected_to_lb:  # Only accept clients if connected to LB
            # The client_start_protocol (UDP part) must complete first for each client.
            # This is a bit convoluted. The original logic implies UDP discovery then TCP connect.
            # In asyncio, the TCP server (start_server) runs independently.
            # We need a way to correlate the UDP discovery with an incoming TCP connection.
            # The original `client_start_protocol` *blocks* until UDP SYN, then *blocks* for TCP accept.
            # Here, `start_server` accepts, then we do handshake.
            # The UDP discovery (`client_start_protocol`) should perhaps just note that a client *might* connect.

            # This loop seems redundant if client_start_protocol is the gate.
            # Let's assume client_start_protocol is now just for the UDP part,
            # and handle_new_connection is the callback for asyncio.start_server.

            # The main loop for accepting clients via TCP is handled by asyncio.start_server itself.
            # This function's role is more to kick off the UDP listening part repeatedly if needed.
            # For now, let's simplify: the TCP server is always running if LB is connected.
            # The UDP discovery is a separate flow.

            # The original `client_connect_protocol` had a loop calling `client_start_protocol` which included accept.
            # With `asyncio.start_server`, `accept` is implicit.
            # We might need a queue or flag that `client_start_protocol` sets.

            # Let's assume the `asyncio.start_server` callback (`handle_new_connection`) is sufficient.
            # This method might not be needed in this form.
            # The `client_start_protocol` should just handle the UDP part.
            # The current design of `client_start_protocol` waits for one UDP and returns.
            # This means `client_connect_protocol` would loop calling it.

            # Revised logic:
            # 1. `run()` starts `lb_connect_protocol`.
            # 2. If LB connects, `run()` starts the TCP server (`asyncio.start_server` with `handle_new_connection`).
            # 3. `run()` also starts a task that *repeatedly* calls `client_start_protocol` to handle UDP discoveries.
            #    `client_start_protocol` no longer returns an ID or handles TCP accept. It just does UDP SYN/SYN-ACK.
            #    The client then connects to the TCP server, and `handle_new_connection` gives it an ID.

            # For now, let client_connect_protocol be the loop that calls client_start_protocol (UDP part)
            # And the TCP server (started in run) handles incoming TCP connections.

            # This task is now just for the UDP discovery part of client connections
            # if await self.client_start_protocol(): # This now only handles UDP discovery
            #     print("Client UDP discovery successful. Awaiting TCP connection.")
            # The TCP connection will be handled by `handle_new_connection`
            # else:
            #     # print("Client UDP discovery failed or timed out.")
            #     await asyncio.sleep(0.1) # Small delay before trying UDP listen again
            # This infinite loop for UDP discovery is better handled by `setup_udp_listener` which is always on.
            # `client_start_protocol` is now effectively integrated into `handle_udp_datagram`.
            # So this `client_connect_listener_task` might be simplified or removed.

            # The primary role of client_connect_protocol was to orchestrate the accept.
            # With asyncio.start_server, this is now handled by the callback.
            # The UDP part is handled by the global UDP listener.

            # This can be a placeholder or removed if all logic moved to handle_new_connection and handle_udp_datagram
            await asyncio.sleep(1)  # Keep it alive if it's run as a persistent task.
        print("No longer listening for new client TCP connections (LB disconnected).")

    async def handle_new_tcp_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        # This is the callback for asyncio.start_server
        client_addr = writer.get_extra_info('peername')
        print(f"New TCP connection from {client_addr}")

        # The original flow: UDP SYN -> UDP SYN-ACK -> Client sends TCP SYN -> Server sends ID -> Client sends ACK for ID (not in code)
        # Here, client connects TCP, server sends ID.
        # We need to check if this client is expected (e.g. from another server, or after UDP discovery)

        # Check if this client_id is expected from another server (moved during gameplay)
        # This requires the client to send its existing ID first upon new connection.
        # Original: server sends "ID", client replies "ID CODE 69;{id}" for *moved* players.
        # Original: server sends "ID CODE 69 {new_id}" for *new* players.

        # Let's simplify: if a client connects, we send an ID request.
        # If it's a *new* client, it won't have an ID to send.
        # If it's a *moved* client, it will send its ID.

        # Ask client for its ID, if it has one (for players moving servers)
        writer.write("ID".encode())  # Ask the client to identify itself
        await writer.drain()

        try:
            data = await asyncio.wait_for(reader.read(1024), timeout=5.0)
            message = data.decode()

            client_id_to_assign = -1

            if message.startswith("ID CODE 69;"):  # Client is reporting an existing ID (moved player)
                existing_client_id = int(message.split(";")[-1])
                print(f"Client {client_addr} reports existing ID: {existing_client_id}")
                # Verify this ID is expected (e.g., in self.moving_servers or a welcome list)
                # For now, accept it.
                async with self.clients_lock:
                    self.connected_clients[existing_client_id] = (client_addr, reader, writer)
                async with self.players_data_lock:  # Ensure player data structure exists
                    if existing_client_id not in self.players_data:
                        self.players_data[existing_client_id] = {}  # Initialize if new to this server instance

                client_id_to_assign = existing_client_id
                # Confirm ID registration
                # writer.write(f"ACK ID {existing_client_id}".encode()) # Optional ack
                # await writer.drain()

            elif message == "NEW":  # Client explicitly states it's new
                print(f"Client {client_addr} is new. Assigning new ID.")
                client_id_to_assign = await self.sendID_to_client(reader, writer, client_addr)

            else:  # Unrecognized initial message, assume new client for now or handle error
                print(f"Client {client_addr} sent unrecognized initial message: '{message}'. Treating as new.")
                client_id_to_assign = await self.sendID_to_client(reader, writer, client_addr)

            if client_id_to_assign != -1:
                print(f"Client {client_addr} assigned/confirmed ID {client_id_to_assign}. Starting handler task.")
                asyncio.create_task(self.handle_client_session(client_id_to_assign, reader, writer, client_addr))
            else:
                print(f"Failed to assign ID to client {client_addr}. Closing connection.")
                writer.close()
                await writer.wait_closed()

        except asyncio.TimeoutError:
            print(f"Timeout waiting for ID from client {client_addr}. Closing connection.")
            writer.close()
            # await writer.wait_closed() # May fail if already closed by peer
        except ConnectionResetError:
            print(f"Connection reset by client {client_addr} during handshake.")
            # writer already closed
        except Exception as e:
            print(f"Error during new client TCP handshake with {client_addr}: {e}")
            if not writer.is_closing():
                writer.close()
                # await writer.wait_closed()

    async def handle_client_session(self, client_id: int, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                                    client_address: Any):
        # Initialize states for this client
        async with self.counter_lock:
            self.players_counter[client_id] = 0
        async with self.elements_lock:  # Ensure structure exists
            self.updated_elements[client_id] = {}
        async with self.players_data_lock:  # Ensure structure exists, might have been set up by sendID or login
            if client_id not in self.players_data or not self.players_data[client_id]:  # e.g. no x,y yet
                # If login is required first, this might be set later by process_login
                # For now, ensure a basic dict
                self.players_data[client_id] = self.players_data.get(client_id, {})

        print(f"Handling client {client_id} at {client_address}")
        try:
            while True:
                if reader.at_eof():
                    print(f"Client {client_id} sent EOF. Closing connection.")
                    break
                data = await reader.read(1024)
                if not data:
                    print(f"Client {client_id} disconnected (no data).")
                    break

                message = data.decode().strip()  # Strip to handle potential extra newlines
                if not message: continue  # Skip empty messages

                # print(f"Client {client_id} sent: {message}")
                exit_cond = await self.process_player_data(client_id, message, writer)  # Pass writer
                if exit_cond == 1:  # KICK
                    print(f"Kicking client {client_id}.")
                    break
        except ConnectionResetError:
            print(f"Connection reset by client {client_address} (ID: {client_id}).")
        except asyncio.IncompleteReadError:
            print(f"Incomplete read from client {client_address} (ID: {client_id}). Connection likely closed.")
        except Exception as e:
            print(f"Error handling client {client_address} (ID: {client_id}): {e}")
        finally:
            print(f"Client {client_address} (ID: {client_id}) disconnected or session ended.")

            # Cleanup logic
            async with self.cache_lock, self.secret_lock:  # Acquire both locks if necessary for atomicity
                if client_id in self.players_cached and client_id in self.secret_players_data:
                    self.players_cached[client_id] = self.secret_players_data[client_id]
                    del self.secret_players_data[client_id]

            async with self.clients_lock:
                if client_id in self.connected_clients:
                    # Get the writer from connected_clients to close it
                    _, _, stored_writer = self.connected_clients[client_id]
                    if not stored_writer.is_closing():
                        stored_writer.close()
                        # await stored_writer.wait_closed() # Consider if necessary, might hang if peer closed abruptly
                    del self.connected_clients[client_id]

            async with self.players_data_lock:
                if client_id in self.players_data:
                    del self.players_data[client_id]

            async with self.counter_lock:
                if client_id in self.players_counter:
                    del self.players_counter[client_id]

            async with self.grid_lock:  # Assuming grid methods are safe
                if client_id in self.grid.player_positions:  # Check existence before removal
                    self.grid.remove_player(client_id)

            async with self.elements_lock:
                self.updated_elements[client_id] = {'disconnect': True}

            # Delayed deletion of 'disconnect' status
            await asyncio.sleep(10)
            async with self.elements_lock:
                if client_id in self.updated_elements and self.updated_elements[client_id].get('disconnect'):
                    del self.updated_elements[client_id]

            if not writer.is_closing():  # Ensure the writer passed to this session handler is also closed
                writer.close()
                # await writer.wait_closed()

    async def process_player_data(self, client_id: int, message: str, writer: asyncio.StreamWriter):
        try:
            messages = message.split(' ', maxsplit=1)
            protocol = messages[0]
            data_payload = messages[1] if len(messages) > 1 else ""

            if protocol in self.protocols:
                # Pass self (SubServer instance), client_id, data_payload, and the writer
                await self.protocols[protocol](self, client_id, data_payload, writer)
            elif protocol in self.receive_protocol:
                async with self.elements_lock:  # Original logic had this here
                    if client_id not in self.updated_elements: self.updated_elements[client_id] = {}
                    # Clearing it here might be problematic if other parts are updating it concurrently
                    # self.updated_elements[client_id] = {} # Clears updates before processing request
                return await self.receive_protocol[protocol](self, client_id, writer)
            else:
                print(f"Unknown protocol '{protocol}' from client {client_id}, ignoring.")
                writer.write("ERROR Unknown protocol\n".encode())  # Send error back
                await writer.drain()

            async with self.counter_lock:  # Reset counter on any valid processed message
                self.players_counter[client_id] = 0
            return 0  # Success, continue session
        except Exception as e:
            print(f"Error processing player data for {client_id} ('{message}'): {e}")
            try:
                writer.write(f"ERROR Processing error: {e}\n".encode())
                await writer.drain()
            except Exception as e_send:
                print(f"Failed to send error to client {client_id}: {e_send}")
            return 0  # Continue session unless error is critical (e.g. kick handled by caller)

    async def create_new_pos(self):
        borders = {
            1: (0, 0),
            2: (self.server_borders[0], 0),
            3: (self.server_borders[0], self.server_borders[1]),
            4: (0, self.server_borders[1])
        }.get(self.server_index, (0, 0))

        x, y = self.get_random_bot_position(borders)
        while True:
            async with self.grid_lock, self.players_data_lock:  # Accessing grid and potentially players_data
                nearby = self.grid.get_nearby_players(x, y, 100)  # Ensure this method is async-safe
                if not nearby:  # Check if empty
                    break
                else:
                    x, y = self.get_random_bot_position(borders)
        return x, y

    async def run(self):
        await self.setup_udp_listener()  # Start UDP listener first
        await self.async_init()

        # Start Load Balancer connection process
        # This will run, connect, and if successful, start self.handle_lb task
        lb_connection_task = asyncio.create_task(self.lb_connect_protocol())

        # Wait for LB connection before starting client services
        while not self.is_connected_to_lb:
            if lb_connection_task.done() and not self.is_connected_to_lb:
                print("Load balancer connection task finished but not connected. Server cannot start client services.")
                # Optionally, retry lb_connection_task or exit
                # For now, let's retry if it failed due to an exception caught in lb_connect_protocol
                if lb_connection_task.exception():
                    print(f"LB connection task failed: {lb_connection_task.exception()}. Retrying...")
                    await asyncio.sleep(5)
                    lb_connection_task = asyncio.create_task(self.lb_connect_protocol())
                else:  # Task done but is_connected_to_lb is false without exception (e.g. clean exit in protocol)
                    print("LB connection attempt concluded without success. Exiting or retrying.")
                    # Decide retry strategy or exit
                    await asyncio.sleep(5)  # Simple retry delay
                    lb_connection_task = asyncio.create_task(self.lb_connect_protocol())

            await asyncio.sleep(1)

        print("Successfully connected to Load Balancer. Starting client services.")

        # Start TCP server for clients
        tcp_server = await asyncio.start_server(
            self.handle_new_tcp_connection,  # раньше был self.client_connect_protocol
            self.server_address[0], self.server_address[1]
        )
        addr = tcp_server.sockets[0].getsockname()
        print(f'TCP Server listening on {addr}')

        # Start Bot Management task
        bots_task = asyncio.create_task(self.BotManage())

        # Keep main tasks running
        # The server will run as long as tcp_server.serve_forever() or equivalent runs.
        # handle_lb runs its own loop. BotManage runs its own loop.
        async with tcp_server:
            await tcp_server.serve_forever()

        # Cleanup if serve_forever exits (e.g., server cancellation)
        bots_task.cancel()
        try:
            await bots_task
        except asyncio.CancelledError:
            print("Bots task cancelled.")

        if self.lb_writer:
            self.lb_writer.close()
            # await self.lb_writer.wait_closed() # Wait for clean close

        if self.udp_transport:
            self.udp_transport.close()

        print("Server shutdown complete.")


if __name__ == "__main__":
    server = SubServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("Server shutting down...")
    except Exception as e:
        print(f"Unhandled error in main: {e}")
    finally:
        # Additional cleanup if needed, though server.run() should handle its tasks
        # For example, ensuring all UDP/TCP sockets are closed if asyncio.run exits early
        if server.udp_transport and not server.udp_transport.is_closing():
            server.udp_transport.close()
        if server.lb_writer and not server.lb_writer.is_closing():
            server.lb_writer.close()
        # Active client writers would be closed by their respective handle_client_session tasks
        # or if the main TCP server is explicitly closed.
        print("Main execution finished.")
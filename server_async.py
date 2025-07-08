import asyncio
import socket
import threading
import random
import time
import json
import os
import pytmx

from scipy.spatial import KDTree
import sub_client_prots_async as sub_client_prots  # Adapted
import sub_lb_prots_async as sub_lb_prots  # Adapted
import bots_async as bots  # Adapted
import players_grid

# Constants
LB_PORT = 5002
UDP_PORT = LB_PORT + 1  # This is for LB discovery in original
CLIENT_DISCOVERY_UDP_PORT = UDP_PORT + 1  # New distinct port for client UDP discovery
SERVER_PORT = 5000
SYN = "SYNC CODE 1"  # For LB
SYN_ACK = "SYNC+ACK CODE 1"  # For LB
ACK = "ACK CODE 2"  # For LB

# Client UDP Handshake Codes (from original client_start_protocol)
CLIENT_SYN_UDP = "SYNC CODE 69"
SERVER_SYN_ACK_UDP = "SYNC+ACK CODE 69"

RADIUS = 600


def get_ip_address():
    if os.environ.get("RUNNING_IN_DOCKER", "0") == "1":
        return "0.0.0.0"
    else:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)


def get_collidable_tiles_optimized(tmx_data):
    collidable_tiles = set()
    for layer in tmx_data.layers:
        if isinstance(layer, pytmx.TiledObjectGroup) and layer.name == "no walk no shoot":
            collidable_tiles.update(
                (obj.x - 500, obj.width, obj.y - 330, obj.height) for obj in layer
            )
    return collidable_tiles


def build_collision_kdtree_optimized(collidable_tiles):
    positions = [(x + w / 2, y - h / 2) for (x, w, y, h) in collidable_tiles]
    if not positions:
        print("Warning: No collidable tiles found to build KD-tree.")
        return KDTree([]), {}
    kd_tree = KDTree(positions, leafsize=16)
    pos_to_tile = {pos: tile for pos, tile in zip(positions, collidable_tiles)}
    return kd_tree, pos_to_tile


class SubServer:
    def __init__(self):
        self.loop = None
        self.server_task = None  # For the main asyncio TCP server
        self.bot_management_task = None  # If needed for a global bot manager task

        # LB Sockets (remain synchronous for LB thread)
        self.lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lb_discovery_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # For LB SYN/ACK
        self.lb_discovery_udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            # This UDP port is for LB discovery
            self.lb_discovery_udp_socket.bind((get_ip_address(), UDP_PORT))
            self.lb_discovery_udp_socket.settimeout(4)
        except OSError as e:
            print(f"🛑 Error binding LB UDP discovery socket ({UDP_PORT}): {e}.")

        # Client Discovery UDP Socket (New)
        self.client_discovery_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # No broadcast needed if clients send directly to server IP
        try:
            self.client_discovery_udp_socket.bind((get_ip_address(), CLIENT_DISCOVERY_UDP_PORT))
            self.client_discovery_udp_socket.settimeout(2)  # Shorter timeout for client pings
            print(f"📡 Client UDP Discovery listening on {get_ip_address()}:{CLIENT_DISCOVERY_UDP_PORT}")
        except OSError as e:
            print(f"🛑 Error binding Client UDP discovery socket ({CLIENT_DISCOVERY_UDP_PORT}): {e}.")

        self.server_address = (get_ip_address(), SERVER_PORT)  # TCP server address
        self.load_balancer_address = (None, LB_PORT)
        self.is_connected_to_lb = False
        self.server_id = 0
        self.server_index = 0
        self.server_borders = [0, 0]

        self.connected_clients = {}
        self.players_data = {}
        self.updated_elements = {}
        self.players_counter = {}

        self.players_to_lb = {}
        self.different_server_players = {}
        self.moving_servers = {}
        self.waiting_login = {}
        self.waiting_register = {}
        self.players_cached = {}
        self.pending_migrating_players = set()
        self.secret_players_data = {}

        self.chat_logs = []
        self.sequence_id = 1

        self.bots = {}
        self.bot_tasks = {}

        # Locks (as previously defined)
        self.clients_lock = asyncio.Lock()
        self.players_data_lock = asyncio.Lock()
        self.elements_lock = asyncio.Lock()
        self.bots_lock = asyncio.Lock()
        self.grid_lock = asyncio.Lock()
        self.counter_lock = asyncio.Lock()
        self.chat_logs_lock = asyncio.Lock()
        self.secret_player_data_async_lock = asyncio.Lock()

        self.lb_data_lock = threading.Lock()
        self.credentials_lock = threading.Lock()
        self.secret_cache_lock = threading.Lock()

        # Protocol Handlers (as previously defined)
        self.protocols = {
            "MOVE": sub_client_prots.process_move_async,
            "SHOOT": sub_client_prots.process_shoot_async,
            "HEALTH": sub_client_prots.process_damage_taken_async,
            "POWER": sub_client_prots.process_power_async,
            "ANGLE": sub_client_prots.process_angle_async,
            "LOGIN": sub_client_prots.process_login_async,
            "REGISTER": sub_client_prots.process_register_async,
            "MONEY": sub_client_prots.process_money_async,
            "AMMO": sub_client_prots.process_ammo_async,
            "INVENTORY": sub_client_prots.process_inventory_async,
            "BOMB": sub_client_prots.process_boom_async,
            "CHAT": sub_client_prots.process_chat_async,
            "DAMAGE": sub_client_prots.process_bot_damage_async,
        }
        self.receive_protocol = {
            "REQUEST": sub_client_prots.process_request_async,
            "REQUESTFULL": sub_client_prots.process_requestFull_async,
        }

        script_dir = os.path.dirname(__file__)
        map_path = os.path.join(script_dir, "map", "map.tmx")
        tmx_data = pytmx.TiledMap(map_path, load_all_tiles=False)
        print("🗺️ Map data loaded successfully.")
        collidable_tiles = get_collidable_tiles_optimized(tmx_data)
        print("🧱 Collidable tiles extracted.")
        self.kd_tree, self.pos_to_tile = build_collision_kdtree_optimized(collidable_tiles)
        if self.kd_tree.data.shape[0] > 0:
            print("🌲 KD-tree built successfully.")
        else:
            print("⚠️ KD-tree is empty. Collision detection might not work as expected.")

        self.grid = players_grid.PlayersGrid(cell_size=1000)
        print("🥅 Player grid initialized.")

    # --- Threadsafe Communication Helper (as previously defined) ---
    def send_to_client_threadsafe(self, client_id, message_bytes):
        async def _send():
            async with self.clients_lock:
                if client_id in self.connected_clients:
                    _reader, writer = self.connected_clients[client_id]
                    if writer and not writer.is_closing():
                        try:
                            writer.write(message_bytes)
                            await writer.drain()
                        except ConnectionResetError:
                            print(f"🔌 (Threadsafe) Connection reset sending to {client_id}.")
                        except Exception as e:
                            print(f"✉️ (Threadsafe) Error sending to {client_id}: {e}")
                    # else: print(f"⚠️ (Threadsafe) Writer for client {client_id} is None/closing.") # Can be verbose
                # else: print(f"❓ (Threadsafe) Client {client_id} not in connected_clients.") # Can be verbose

        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(_send(), self.loop)
        # else: print(f"🚫 (Threadsafe) Asyncio loop not available for {client_id}.") # Can be verbose

    # --- Bot Management (Async - as previously defined) ---
    async def set_bots(self, amount):
        print(f"Setting up {amount} bots...")
        borders = {
            1: (0, 0), 2: (self.server_borders[0], 0),
            3: self.server_borders, 4: (0, self.server_borders[1])
        }.get(self.server_index, (0, 0))

        map_width = self.server_borders[0] if self.server_borders[0] > 0 else 100
        map_height = self.server_borders[1] if self.server_borders[1] > 0 else 100

        async with self.bots_lock, self.players_data_lock, self.elements_lock, self.grid_lock:
            current_bot_ids = set(self.bots.keys())
            new_bot_id_counter = max(current_bot_ids, default=-1) + 1

            for i in range(amount):
                bot_id_to_assign = new_bot_id_counter + i
                new_x, new_y = self._get_random_bot_position(borders, map_width, map_height)
                attempts = 0
                while self.grid.get_nearby_players(new_x, new_y, 50) and attempts < 100:
                    new_x, new_y = self._get_random_bot_position(borders, map_width, map_height)
                    attempts += 1
                if attempts >= 100:
                    print(f"⚠️ Could not find a clear spot for bot {bot_id_to_assign}. Placing anyway.")
                print(f"🤖 Spawning bot {bot_id_to_assign} at ({new_x}, {new_y})")
                is_long_range = random.random() < 0.5
                bot = bots.Bot(new_x, new_y, is_long_range, self.kd_tree, self.pos_to_tile, self.loop, bot_id_to_assign,
                               self)
                self.bots[bot_id_to_assign] = bot
                self.players_data[bot_id_to_assign] = {
                    'x': new_x, 'y': new_y, 'type': "long_range" if is_long_range else "short_range",
                    'angle': 0, 'health': bot.hp, 'bot': True
                }
                if bot_id_to_assign not in self.updated_elements: self.updated_elements[bot_id_to_assign] = {}
                self.grid.add_player(bot_id_to_assign, new_x, new_y)
                task = self.loop.create_task(bot.run_main_logic())
                self.bot_tasks[bot_id_to_assign] = task
        num_bots_set = len(self.bots)
        print(f"🤖 {num_bots_set} bots are now set up and running.")

    def _get_random_bot_position(self, base_borders, map_width, map_height):
        effective_width = max(0, map_width)
        effective_height = max(0, map_height)
        bot_x = base_borders[0] + random.randint(0, effective_width)
        bot_y = base_borders[1] + random.randint(0, effective_height)
        return bot_x, bot_y

    def update_bot_data_in_server(self, bot_id, data_updates):
        async def _update():
            async with self.players_data_lock, self.elements_lock:
                if bot_id not in self.bots or bot_id not in self.players_data:
                    return
                for key, value in data_updates.items():
                    if key in ['x', 'y', 'health', 'angle', 'moving', 'shooting']:
                        self.players_data[bot_id][key] = value
                if 'x' in data_updates or 'y' in data_updates:
                    async with self.grid_lock:
                        self.grid.add_player(bot_id, self.players_data[bot_id]['x'], self.players_data[bot_id]['y'])
                if bot_id not in self.updated_elements: self.updated_elements[bot_id] = {}
                for key, value in data_updates.items():
                    self.updated_elements[bot_id][key] = value

            #print(f"🔄 Updated bot {bot_id} data in server: {data_updates}")

        if self.loop and self.loop.is_running():
            self.loop.create_task(_update())

    def clear_bot_data(self, bot_id):
        async def _clear():
            async with self.players_data_lock, self.elements_lock, self.grid_lock:
                if bot_id in self.updated_elements:
                    self.updated_elements[bot_id] = {}
            print(f"🗑️ Cleared data for bot {bot_id}.")

        if self.loop and self.loop.is_running():
            self.loop.create_task(_clear())

    async def restart_bot(self, bot_id_to_replace):
        print(f"🔄 Restarting bot (ID was {bot_id_to_replace})...")
        async with self.bots_lock, self.players_data_lock, self.elements_lock, self.grid_lock:
            if bot_id_to_replace in self.bot_tasks and self.bot_tasks[bot_id_to_replace]:
                self.bot_tasks[bot_id_to_replace].cancel()
                try:
                    await self.bot_tasks[bot_id_to_replace]
                except asyncio.CancelledError:
                    pass
                del self.bot_tasks[bot_id_to_replace]
            if bot_id_to_replace in self.bots: del self.bots[bot_id_to_replace]
            if bot_id_to_replace in self.players_data: del self.players_data[bot_id_to_replace]
            if bot_id_to_replace in self.updated_elements: del self.updated_elements[bot_id_to_replace]
            if bot_id_to_replace in self.grid.player_positions: self.grid.remove_player(bot_id_to_replace)
        await asyncio.sleep(random.uniform(2, 6))
        print(f"Spawning a new bot to replace former ID {bot_id_to_replace}.")
        await self.set_bots(1)

    def handle_bot_death(self, bot_id):
        async def _process_death():
            print(f"💀 Bot {bot_id} has died.")
            async with self.players_data_lock, self.elements_lock:
                if bot_id in self.players_data:
                    self.players_data[bot_id]['health'] = 0
                    self.players_data[bot_id]['dead'] = True
                if bot_id in self.updated_elements:
                    self.updated_elements[bot_id]['health'] = 0
                    self.updated_elements[bot_id]['dead'] = True
            self.loop.create_task(self.restart_bot(bot_id))

        if self.loop and self.loop.is_running():
            self.loop.create_task(_process_death())

    def CheckIfMoving(self, client_id):
        if client_id in self.moving_servers.keys():
            return True, self.moving_servers[client_id]
        else:
            return False, 0

    async def trigger_bots_near_player(self, player_x, player_y, player_id):
        bots_to_alert = []
        print(f"🔍 Triggering bots near player {player_id} at ({player_x}, {player_y})")
        async with self.grid_lock:
            nearby_bots = self.grid.get_nearby_players(player_x, player_y, 5000)
            nearby_bots = [bot_id for bot_id in nearby_bots if bot_id in self.bots]
            for bot_id in nearby_bots:
                if bot_id in self.bots and bot_id != player_id:
                    bots_to_alert.append(bot_id)

        if bots_to_alert:
            async with self.bots_lock:
                for bot_id in bots_to_alert:
                    if bot_id in self.bots:
                        bot = self.bots[bot_id]
                        print(f"🔔 Alerting bot {bot_id} to player {player_id}'s position.")
                        bot.send_target(player_x, player_y, player_id)
                        await asyncio.sleep(0.01)  # Yield control to allow other tasks

    async def create_new_pos_async(self):  # Made async to use grid_lock properly
        borders = {
            1: (0, 0), 2: (self.server_borders[0], 0),
            3: self.server_borders, 4: (0, self.server_borders[1])
        }.get(self.server_index, (0, 0))

        map_width = self.server_borders[0] if self.server_borders[0] > 0 else 100
        map_height = self.server_borders[1] if self.server_borders[1] > 0 else 100

        attempts = 0
        while attempts < 100:
            x, y = self._get_random_bot_position(borders, map_width, map_height)
            async with self.grid_lock:  # Correctly use async lock
                is_occupied = self.grid.get_nearby_players(x, y, 50)
            if not is_occupied:
                return x, y
            attempts += 1
        print("⚠️ create_new_pos_async failed to find an empty spot.")
        return borders[0] + map_width // 2, borders[1] + map_height // 2

        # --- Client UDP Discovery and Initial Handshake ---

    def _client_udp_discovery_thread_function(self):
        print(f"🚦 Client UDP Discovery Thread: Starting on port {CLIENT_DISCOVERY_UDP_PORT}...")
        while getattr(self, 'keep_running', True):
            try:
                data, client_addr = self.client_discovery_udp_socket.recvfrom(1024)
                message = data.decode()
                # print(f"📡 Client UDP Discovery: Received '{message}' from {client_addr}")

                if message == CLIENT_SYN_UDP:  # "SYNC CODE 69"
                    # Respond with SYN+ACK and TCP server address
                    response = f"{SERVER_SYN_ACK_UDP} {self.server_address[0]};{self.server_address[1]}".encode()
                    self.client_discovery_udp_socket.sendto(response, client_addr)
                    print(f"📬 Client UDP Discovery: Sent SYN+ACK to {client_addr} with TCP {self.server_address}")
                # The original sendID() and AskForID() were for TCP after this.
                # The asyncio TCP server now handles ID assignment on connection.
            except socket.timeout:
                continue  # Just loop again
            except OSError as e:  # Socket might be closed during shutdown
                if getattr(self, 'keep_running', True):  # Avoid error message if intentionally stopping
                    print(f"🛑 Client UDP Discovery Thread: Socket error: {e}")
                break  # Exit thread on major socket error
            except Exception as e:
                print(f"💥 Client UDP Discovery Thread: Unexpected error: {e}")
        print("🏁 Client UDP Discovery Thread: Finished.")

    # --- TCP Client Handling (Async - as previously defined) ---
    async def handle_client_async(self, reader, writer):
        # This function remains largely the same as the previous refactor.
        # Key difference: Client ID is now assigned here directly, not via prior UDP handshake for ID.
        # The UDP discovery is just for clients to find the TCP server address.
        addr = writer.get_extra_info('peername')
        print(f"🤝 New TCP connection from {addr} (result of UDP discovery or direct connect)")
        client_id = -1
        exit_code_signal = 0

        try:
            async with self.clients_lock:
                client_id = random.randint(20001, 30000)  # Separate range from bots
                while client_id in self.connected_clients or client_id in self.bots:
                    client_id = random.randint(20001, 30000)
                self.connected_clients[client_id] = (reader, writer)

            print(f"Assigned Client ID {client_id} to TCP connection {addr}")

            # Send the formal ID assignment via TCP (as per original AskForID/SendID logic for TCP part)
            # The client, after UDP SYN+ACK, connects to TCP and *then* gets this ID.
            writer.write(f"ID CODE 69 {client_id}".encode())
            await writer.drain()
            print(f"Sent TCP ID {client_id} to {addr}")

            async with self.players_data_lock, self.elements_lock, self.counter_lock:
                temp_x, temp_y = 0, 0
                self.players_data[client_id] = {'x': temp_x, 'y': temp_y, 'health': 100, 'angle': 0, 'bot': False}
                self.updated_elements[client_id] = {}
                self.players_counter[client_id] = 0

            while True:
                if writer.is_closing(): break
                try:
                    data = await asyncio.wait_for(reader.read(2048), timeout=300.0)
                except asyncio.TimeoutError:
                    print(f"Client {client_id} timed out.")
                    if not writer.is_closing(): writer.write(b"KICK_INACTIVE\n"); await writer.drain()
                    break

                if not data:
                    print(f"Client {client_id} ({addr}) disconnected (TCP).")
                    break

                message_decoded = data.decode().strip()
                for single_message in message_decoded.split('\n'):
                    if not single_message.strip(): continue
                    exit_code_signal = await self.process_player_data_async(client_id, writer, single_message)
                    if exit_code_signal == 1: break
                if exit_code_signal == 1: break

                await asyncio.sleep(0.05)  # Yield control to allow other tasks

        except ConnectionResetError:
            print(f"🔌 Client {client_id} ({addr}) reset TCP connection.")
        except asyncio.IncompleteReadError:
            print(f"💔 Client {client_id} ({addr}) TCP disconnected (incomplete read).")
        except Exception as e:
            print(f"💥 Error handling TCP client {client_id} ({addr}): {type(e).__name__} - {e}")
        finally:
            print(f"🧼 Cleaning up for TCP client {client_id} from {addr}.")
            async with self.clients_lock:
                if client_id in self.connected_clients: del self.connected_clients[client_id]

            async with self.players_data_lock, self.elements_lock, self.grid_lock, self.counter_lock:
                if client_id in self.players_data: del self.players_data[client_id]
                if client_id in self.grid.player_positions: self.grid.remove_player(client_id)
                if client_id in self.players_counter: del self.players_counter[client_id]
                if client_id != -1:
                    if client_id not in self.updated_elements: self.updated_elements[client_id] = {}
                    self.updated_elements[client_id]['disconnect'] = True

            player_secret_data_snapshot = None
            async with self.secret_player_data_async_lock:
                if client_id in self.secret_players_data:
                    player_secret_data_snapshot = self.secret_players_data.pop(client_id, None)
            if player_secret_data_snapshot:
                with self.secret_cache_lock:
                    self.players_cached[client_id] = player_secret_data_snapshot

            if writer and not writer.is_closing():
                try:
                    writer.close(); await writer.wait_closed()
                except Exception as e_close:
                    print(f"Error closing writer for {client_id}: {e_close}")
            print(f"Client {client_id} ({addr}) TCP connection fully closed and cleaned up.")

    async def process_player_data_async(self, client_id, writer, message: str):
        # (As previously defined, ensure it calls adapted sub_client_prots)
        try:
            parts = message.split(' ', 1)
            protocol = parts[0]
            data_payload = parts[1] if len(parts) > 1 else ""

            if protocol in self.protocols:
                handler = self.protocols[protocol]
                # Pass server, client_id, writer, and payload
                await handler(self, client_id, writer, data_payload)  # Ensure handler is async
            elif protocol in self.receive_protocol:
                async with self.elements_lock:
                    self.updated_elements[client_id] = {}  # Reset for new request
                handler = self.receive_protocol[protocol]
                kick_signal = await handler(self, client_id, writer)  # Ensure handler is async
                if kick_signal == 1:
                    return 1
            else:
                print(f"🤷 Unknown protocol from {client_id}: {protocol}")
                if writer and not writer.is_closing():
                    writer.write(f"ERR_UNKNOWN_PROTOCOL {protocol}\n".encode())
                    await writer.drain()
            return 0
        except Exception as e:
            print(f"Error in process_player_data_async for {client_id} (msg: '{message}'): {e}")
            return 0

            # --- Main Server Orchestration (as previously defined, but with new thread) ---

    async def _run_main_async_loop(self):
        # (This method remains the same, starting the TCP server and bot management)
        self.loop = asyncio.get_running_loop()
        try:
            server = await asyncio.start_server(
                self.handle_client_async, self.server_address[0], self.server_address[1])
            addr = server.sockets[0].getsockname()
            print(f'🚀 TCP Server serving on {addr} for clients...')
            self.server_task = self.loop.create_task(server.serve_forever())
        except OSError as e:
            print(f"🛑 Failed to start TCP server on {self.server_address}: {e}. Server cannot start.")
            return

        try:
            await self.server_task
        except asyncio.CancelledError:
            print("Main TCP server task cancelled.")
        finally:
            print("Cleaning up bot tasks...")
            async with self.bots_lock:
                for bot_id, task in list(self.bot_tasks.items()):
                    if task and not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                        except Exception as e_bot_cleanup:
                            print(f"Error during bot {bot_id} task cleanup: {e_bot_cleanup}")
            print("All bot tasks processed for cleanup.")
            if server:
                server.close()
                await server.wait_closed()
                print("TCP Server closed.")

    def _lb_thread_function(self):
        # (This method remains the same, using self.lb_discovery_udp_socket for LB)
        print("🚦 LB Thread: Starting...")
        print(f"📡 LB Thread: Listening on UDP {get_ip_address()}:{UDP_PORT} for load balancer broadcast.")
        connected_via_udp = False
        while not connected_via_udp and getattr(self, 'keep_running', True):
            try:
                data_udp, _lb_addr_udp = self.lb_discovery_udp_socket.recvfrom(1024)  # Use dedicated LB UDP socket
                # print(f"📡 LB Thread: Received UDP packet: {data_udp.decode()}") # Can be verbose
                if sub_lb_prots.readSYNcLB(self, data_udp):
                    sub_lb_prots.sendSYNCACKLB(self)
                    if sub_lb_prots.recvACKLB(self):
                        self.is_connected_to_lb = True
                        connected_via_udp = True
                        print(f"✅ LB Thread: Successfully connected to LB. Server ID: {self.server_id}")
                        break
                        # else: print("📡 LB Thread: UDP packet not a valid SYNC from LB or connection failed.") # Can be verbose
            except socket.timeout:
                pass  # print("⏳ LB Thread: UDP discovery timeout. Still waiting for LB...") # Can be verbose
            except Exception as e:
                print(f"🛑 LB Thread: Error in UDP discovery/connect protocol: {e}")
                self.lb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                time.sleep(2)

        if not self.is_connected_to_lb:
            print("🛑 LB Thread: Failed to connect to Load Balancer via UDP. LB communication will not proceed.")
            return

        try:
            sub_lb_prots.getINDEX(self)
            sub_lb_prots.getBORDERS(self)
            print(f"🗺️ LB Thread: Server Index: {self.server_index}, Borders: {self.server_borders}")
            if self.loop and self.loop.is_running() and self.server_borders[0] > 0 and self.server_borders[1] > 0:
                asyncio.run_coroutine_threadsafe(self.set_bots(25), self.loop)
            else:
                print("⚠️ LB Thread: Cannot set bots. Asyncio loop not ready or server borders invalid.")

            while self.is_connected_to_lb and getattr(self, 'keep_running', True):
                sub_lb_prots.SendLogin(self)
                sub_lb_prots.SendRegister(self)
                sub_lb_prots.SendCache(self)
                #sub_lb_prots.SendInfoLB(self)
                #sub_lb_prots.getRIGHT(self)
                #sub_lb_prots.getSEND(self)
                time.sleep(0.2)
        except (socket.error, ConnectionResetError, BrokenPipeError) as sock_err:
            print(f"💔 LB Thread: Socket error during LB communication: {sock_err}. Disconnecting from LB.")
        except Exception as e:
            print(f"💥 LB Thread: Unexpected error during LB handling: {e}")
        finally:
            self.is_connected_to_lb = False
            if self.lb_socket:
                try:
                    self.lb_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                self.lb_socket.close()
            print("🏁 LB Thread: Finished.")

    def run(self):
        self.keep_running = True

        # Thread for Load Balancer communication
        lb_comm_thread = threading.Thread(target=self._lb_thread_function, daemon=True, name="LBThread")
        lb_comm_thread.start()

        # Thread for Client UDP Discovery
        client_udp_thread = threading.Thread(target=self._client_udp_discovery_thread_function, daemon=True,
                                             name="ClientUDPDiscoveryThread")
        client_udp_thread.start()

        try:
            asyncio.run(self._run_main_async_loop())
        except KeyboardInterrupt:
            print("\n🛑 KeyboardInterrupt received. Initiating server shutdown...")
        finally:
            print("Shutting down all components...")
            self.keep_running = False

            if self.server_task and not self.server_task.done():
                self.server_task.cancel()

            # Wait for threads to finish
            if client_udp_thread.is_alive():
                print("Waiting for Client UDP Discovery thread to finish...")
                client_udp_thread.join(timeout=3.0)
                if client_udp_thread.is_alive(): print("Client UDP Discovery thread did not finish in time.")

            if lb_comm_thread.is_alive():
                print("Waiting for LB thread to finish...")
                lb_comm_thread.join(timeout=5.0)
                if lb_comm_thread.is_alive(): print("LB thread did not finish in time.")

            # Close UDP sockets explicitly if they are still open
            try:
                self.lb_discovery_udp_socket.close()
            except Exception:
                pass
            try:
                self.client_discovery_udp_socket.close()
            except Exception:
                pass

            print("✅ Server shutdown complete.")


if __name__ == "__main__":
    try:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        import pygame

        pygame.init()
        print("🎮 Pygame initialized headlessly (if used for collision).")
    except Exception as e:
        print(f"⚠️ Pygame init failed or not found: {e}. Collision may be affected if it uses pygame.")

    server = SubServer()
    server.run()
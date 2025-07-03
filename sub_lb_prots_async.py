import json
import threading
import socket
import asyncio  # For type hinting if needed, not for running async code here

# Constants from original server (ensure they are consistent if used)
SYN = "SYNC CODE 1"
SYN_ACK = "SYNC+ACK CODE 1"
ACK = "ACK CODE 2"
LB_PORT = 5002


# --- Helper for SubServer to send messages to clients from LB thread ---
# This function should be part of your SubServer class in server_async.py
# def send_to_client_threadsafe(self, client_id, message_bytes):
#     async def _send():
#         # Using server.clients_lock (asyncio.Lock)
#         async with self.clients_lock: # Ensure connected_clients dict is accessed safely
#             if client_id in self.connected_clients:
#                 _reader, writer = self.connected_clients[client_id]
#                 if writer and not writer.is_closing():
#                     writer.write(message_bytes)
#                     await writer.drain()
#                 else:
#                     print(f"Threadsafe send: Writer for {client_id} is None or closing.")
#             else:
#                 print(f"Threadsafe send: Client {client_id} not found in connected_clients.")
#
#     if self.loop and self.loop.is_running():
#         asyncio.run_coroutine_threadsafe(_send(), self.loop)
#     else:
#         print(f"Threadsafe send: Asyncio loop not available for client {client_id}.")

# --- LB Protocol Functions (Remain largely synchronous, using threading locks) ---

def readSYNcLB(server, data):  # No change needed, uses server.lb_socket directly
    str_data = data.decode()
    if str_data.startswith(SYN):
        try:
            parts = str_data.split(" ")[-1].split(",")
            lb_ip_part = parts[0]  # Should be like "IP,PORT"
            lb_ip = lb_ip_part.split(';')[1]  # Check this parsing logic
            lb_port_part = parts[1]
            lb_port = lb_port_part.split(';')[1]  # Should be like "PORT;port_val"
            lb_port = int(lb_port)  # Ensure this matches "PORT"

            # Original parsing: str_data.split(" ")[-1].split(",")[0].split(";")[1]
            # This seems overly complex. If format is "SYNC CODE 1 IP;ip_val,PORT;port_val"
            # Simpler example: "SYNC CODE 1 IP:127.0.0.1,PORT:5002"
            # Then parse based on that. The provided parsing is kept but seems fragile.
            # Assuming original parsing was correct for its specific format:
            # lb_ip, lb_port = str_data.split(" ")[-1].split(",")[0].split(";")[1], int(
            #     str_data.split(" ")[-1].split(",")[1].split(";")[1])

        except IndexError or ValueError as e:
            print(f"Error parsing SYNC from LB: {str_data}, {e}")
            return False

        if lb_port == LB_PORT:
            try:
                server.load_balancer_address = (lb_ip, lb_port)
                server.lb_socket.connect(server.load_balancer_address)
                print(f"LB Comms: SYNC Success, connected to LB at {server.load_balancer_address}")
                return True
            except Exception as e:
                print(f"LB Comms: Error connecting to load balancer: {e}")
    return False


def sendSYNCACKLB(server):  # No change
    server.lb_socket.send(SYN_ACK.encode())


def recvACKLB(server):  # No change
    data = server.lb_socket.recv(1024).decode()
    if data.startswith(ACK):
        print("LB Comms: Received ACK from LB")
        server.server_id = int(data.split(";")[-1])
        print("LB Comms: Server ID:", server.server_id)
        return True
    return False


def getINDEX(server):  # No change
    server.lb_socket.send("INDEX".encode())
    data = server.lb_socket.recv(1024).decode()
    if data.startswith("INDEX CODE 2"):
        server.server_index = int(data.split(";")[-1])
        print("LB Comms: Server INDEX:", server.server_index)
    else:
        print("LB Comms: Failed to get server INDEX from load balancer, error:", data)


def getBORDERS(server):  # No change
    server.lb_socket.send("BORDERS".encode())
    data = server.lb_socket.recv(1024).decode()
    if data.startswith("BORDERS CODE 2"):
        data_payload = data.split()[-1]  # Get the last part "X;Y"
        server.server_borders[0] = int(float(data_payload.split(";")[0]))
        server.server_borders[1] = int(float(data_payload.split(";")[1]))
        print("LB Comms: Server BORDERS:", server.server_borders)
    else:
        print("LB Comms: Failed to get server BORDERS from load balancer, error:", data)


def AddToLB(server, client_id):
    # players_data is asyncio.Lock protected. Read via threadsafe call or ensure LB only reads snapshots.
    # For now, assume this is called when player data is stable or needs explicit async read.
    # This function is problematic if server.players_data[client_id] is read directly
    # while it's being modified by asyncio loop.
    # Safest: LB thread signals asyncio loop to get data and queue it for LB.
    # Simplified: direct read with threading.Lock if players_data used threading.Lock
    # BUT players_data uses asyncio.Lock.
    # This requires a call to the asyncio loop to get the data.

    # Solution: Server method to get player data for LB thread-safely
    # async def get_player_data_for_lb(self, client_id):
    #     async with self.players_data_lock:
    #         return self.players_data.get(client_id, {}).copy()
    # player_info_future = asyncio.run_coroutine_threadsafe(server.get_player_data_for_lb(client_id), server.loop)
    # info = player_info_future.result() # Blocking call

    # For this adaptation, let's assume a (less safe) direct read, implying players_data access
    # from LB thread needs extreme care or a different locking strategy if this is frequent.
    # The original used server.players_data directly.
    # This implies server.players_data_lock should be a threading.Lock if LB writes to it.
    # But for game logic, asyncio.Lock is better. This is a conflict point.
    # Assuming AddToLB is for sending data that LB *reads*, and players_data_lock is asyncio.Lock:
    # This function can't directly access players_data safely if it's under an asyncio.Lock.
    # The data should be prepared by an asyncio task and put into players_to_lb.
    # For now, will keep structure but highlight this as needing robust solution.

    # TEMPORARY: This is not fully safe.
    # info = server.players_data.get(client_id, {}).copy() # Needs proper async retrieval
    # This function is called from process_move_async, which HAS safe access.
    # So the `info` should be passed to `AddToLB` or `CheckForLB` should pass the data.

    # Let's redefine CheckForLB to pass necessary info from players_data
    # And AddToLB will just use the passed info.
    # This is a significant change from original structure but safer.
    pass  # AddToLB will now take the data directly.


def CheckForLB(server, client_id, x, y):  # player_data_snapshot from asyncio context
    # This function itself doesn't need to be async, it's logic.
    # It uses server.lb_data_lock (threading.Lock) for players_to_lb.
    moved_server = False
    if server.server_index == 1:
        if x > server.server_borders[0] or y > server.server_borders[1]: moved_server = True
    elif server.server_index == 2:  # Corrected logic for index 2 (original seemed to be copy-paste)
        if x < server.server_borders[0] or y > server.server_borders[
            1]: moved_server = True  # Example: top-right server
    elif server.server_index == 3:
        if x < server.server_borders[0] or y < server.server_borders[1]: moved_server = True
    elif server.server_index == 4:
        if x > server.server_borders[0] or y < server.server_borders[1]: moved_server = True

    if moved_server:
        info_for_lb = server.updated_elements.copy()  # Use the snapshot
        info_for_lb['server'] = server.server_id  # Add current server_id
        with server.lb_data_lock:  # This is server.players_to_lb_lock (threading.Lock)
            server.players_to_lb[client_id] = info_for_lb
            print(f"LB Comms: Client {client_id} marked for LB due to crossing border.")


def SendInfoLB(server):  # players_to_lb is protected by lb_data_lock
    with server.lb_data_lock:
        if not server.players_to_lb:
            # Send heartbeat or empty INFO if protocol requires it, otherwise skip.
            # For now, skip if empty.
            return
        message_to_send = ("INFO " + json.dumps(server.players_to_lb)).encode()
        # Clear after preparing, or after ACK from LB
        # server.players_to_lb.clear() # Option 1: clear optimistically

    server.lb_socket.send(message_to_send)
    data = server.lb_socket.recv(1024).decode()  # Blocking
    if data == "ACK":
        with server.lb_data_lock:  # Option 2: clear after ACK
            server.players_to_lb.clear()
        return
    else:
        print(f"LB Comms: Failed to send INFO data to load balancer, error: {data}")
        # Decide on retry or re-queuing data in server.players_to_lb
        return


def getRIGHT(server):  # Manages moving_servers, calls WelcomePlayers (problematic)
    server.lb_socket.send(f"RIGHT".encode())
    data_json = server.lb_socket.recv(1024).decode()  # Blocking
    data = json.loads(data_json)

    players_to_welcome_here = []  # List of client_ids LB says should be on this server

    with server.lb_data_lock:  # Protects server.moving_servers
        # server.moving_servers could be cleared here or selectively updated
        # server.moving_servers.clear() # If data from LB is the new source of truth
        for client_id_str, destination_server_ip_or_true in data.items():
            client_id = int(client_id_str)  # Assuming client_id from LB is string
            if destination_server_ip_or_true is True:  # True means player should connect to this server
                players_to_welcome_here.append(client_id)
            else:  # It's an IP for another server
                server.moving_servers[client_id] = destination_server_ip_or_true

    if players_to_welcome_here:
        print(f"LB Comms: Instructed to welcome players: {players_to_welcome_here}")
        # The original WelcomePlayers started a new thread with a blocking accept loop.
        # This is not how asyncio server works.
        # For now, this list could be stored, and when a client connects and authenticates,
        # if their ID is in this list, their state is restored.
        # A proper "player migration" protocol is needed.
        # This call is removed as WelcomePlayers in its original form is not compatible.
        # welcome_thread = threading.Thread(target=server.WelcomePlayers, args=(players_to_welcome_here,))
        # welcome_thread.start()
        # Instead, store them:
        with server.lb_data_lock:  # Or a new lock for this specific list
            server.pending_migrating_players.update(players_to_welcome_here)  # server.pending_migrating_players is new


def getSEND(server):  # Populates different_server_players
    with server.lb_data_lock:  # Assuming different_server_players also uses lb_data_lock
        server.different_server_players.clear()  # Clear old data
        server.lb_socket.send(f"SEND".encode())
        data_json = server.lb_socket.recv(1024).decode()  # Blocking
        try:
            data = json.loads(data_json)
            server.different_server_players = data  # This should be a dict client_id -> data
        except json.JSONDecodeError:
            print(f"LB Comms: Failed to decode JSON from SEND response: {data_json}")


def SendLogin(server):  # Uses credentials_lock (threading.Lock)
    try:
        login_data_snapshot = None
        with server.credentials_lock:
            if not server.waiting_login:
                return
            login_data_snapshot = server.waiting_login.copy()
            server.waiting_login.clear()  # Clear after copying

        if login_data_snapshot:
            str_login = f"LOGIN {json.dumps(login_data_snapshot)}"
            print(f"LB Comms: Sending login data: {str_login}")
            server.lb_socket.send(str_login.encode())

            response_data_json = server.lb_socket.recv(1024).decode()  # Blocking
            response_data = json.loads(response_data_json)
            SortLogin(server, response_data)  # Call SortLogin to process LB's response

    except socket.timeout:
        print("LB Comms: No data received from LB for LOGIN within timeout period")
        # Re-queue login_data_snapshot if needed, or handle failure
    except json.JSONDecodeError:
        print(
            f"LB Comms: Failed to decode JSON from LOGIN response: {response_data_json if 'response_data_json' in locals() else 'Unknown'}")
    except Exception as e:
        print(f"LB Comms: Error in SendLogin: {e}")


def SortLogin(server, data_from_lb):  # data_from_lb is dict: {client_id_str: [protocol_str, payload_dict]}
    for client_id_str, response_parts in data_from_lb.items():
        client_id = int(client_id_str)
        protocol_msg = response_parts[0]
        payload = response_parts[1] if len(response_parts) > 1 else None

        if protocol_msg.startswith("SUCCESS CODE LOGIN"):
            print(f"LB Comms: Login for client {client_id} successful!")

            # Update secret_players_data (this needs care if it's an asyncio managed dict)
            # Assuming secret_player_data_async_lock is asyncio.Lock
            async def _update_secret_and_player_data():
                async with server.secret_player_data_async_lock:
                    server.secret_players_data[client_id] = payload  # payload is the player's data from DB

                # Create new position and update players_data (asyncio domain)
                new_x, new_y = await server.create_new_pos_async()
                async with server.players_data_lock:  # asyncio.Lock
                    if client_id not in server.players_data: server.players_data[client_id] = {}
                    server.players_data[client_id]['x'] = new_x
                    server.players_data[client_id]['y'] = new_y
                    # Also update other relevant fields from payload into server.players_data
                    server.players_data[client_id]['health'] = payload.get("PlayerHealth", 100)  # Example

                # Prepare data to send to client (includes new x, y)
                data_to_send_client = payload.copy()
                data_to_send_client['x'] = new_x
                data_to_send_client['y'] = new_y
                return f"SUCCESS CODE LOGIN {json.dumps(data_to_send_client)}".encode()

            future = asyncio.run_coroutine_threadsafe(_update_secret_and_player_data(), server.loop)
            message_bytes_to_client = future.result()  # Blocking wait for the result
            server.send_to_client_threadsafe(client_id, message_bytes_to_client)

        elif protocol_msg.startswith("FAILED CODE LOGIN"):
            print(f"LB Comms: Login for client {client_id} failed: {protocol_msg}")
            server.send_to_client_threadsafe(client_id, f"{protocol_msg}\n".encode())


def SendRegister(server):  # Uses credentials_lock (threading.Lock)
    try:
        register_data_snapshot = None
        with server.credentials_lock:
            if not server.waiting_register:
                return
            register_data_snapshot = server.waiting_register.copy()
            server.waiting_register.clear()

        if register_data_snapshot:
            str_register = f"REGISTER {json.dumps(register_data_snapshot)}"
            print(f"LB Comms: Sending register data: {str_register}")
            server.lb_socket.send(str_register.encode())

            response_data_json = server.lb_socket.recv(1024).decode()  # Blocking
            response_data = json.loads(response_data_json)
            SortRegister(server, response_data)

    except socket.timeout:
        print("LB Comms: No data received from LB for REGISTER within timeout period")
    except json.JSONDecodeError:
        print(
            f"LB Comms: Failed to decode JSON from REGISTER response: {response_data_json if 'response_data_json' in locals() else 'Unknown'}")
    except Exception as e:
        print(f"LB Comms: Error in SendRegister: {e}")


def SortRegister(server, data_from_lb):
    for client_id_str, response_parts in data_from_lb.items():
        client_id = int(client_id_str)
        protocol_msg = response_parts[0]
        payload = response_parts[1] if len(response_parts) > 1 else None

        if protocol_msg.startswith("SUCCESS CODE REGISTER"):
            print(f"LB Comms: Register for client {client_id} successful!")

            async def _update_secret_and_player_data_register():
                async with server.secret_player_data_async_lock:  # asyncio.Lock
                    server.secret_players_data[client_id] = payload  # payload is new player data

                new_x, new_y = await server.create_new_pos_async()  # Sync server method
                async with server.players_data_lock:  # asyncio.Lock
                    if client_id not in server.players_data: server.players_data[client_id] = {}
                    server.players_data[client_id]['x'] = new_x
                    server.players_data[client_id]['y'] = new_y
                    server.players_data[client_id]['health'] = payload.get("PlayerHealth", 100)  # Example default

                data_to_send_client = payload.copy()
                data_to_send_client['x'] = new_x
                data_to_send_client['y'] = new_y
                return f"SUCCESS CODE REGISTER {json.dumps(data_to_send_client)}".encode()

            future = asyncio.run_coroutine_threadsafe(_update_secret_and_player_data_register(), server.loop)
            message_bytes_to_client = future.result()
            server.send_to_client_threadsafe(client_id, message_bytes_to_client)

        elif protocol_msg.startswith("FAILED CODE REGISTER"):
            # Enhance error message based on code from original if needed
            result_msg = protocol_msg
            if protocol_msg == "FAILED CODE REGISTER 2":
                result_msg = "FAILED CODE REGISTER User already exists, try logging in"
            elif protocol_msg == "FAILED CODE REGISTER 3":
                result_msg = "FAILED CODE REGISTER Username already taken, try another one"
            print(f"LB Comms: Register for client {client_id} failed: {result_msg}")
            server.send_to_client_threadsafe(client_id, f"{result_msg}\n".encode())


def SendCache(server):  # Uses server.secret_cache_lock (threading.Lock)
    try:
        cached_data_snapshot = None
        with server.secret_cache_lock:  # Original used self.cache_lock, renamed for clarity
            if not server.players_cached:
                return
            cached_data_snapshot = server.players_cached.copy()
            server.players_cached.clear()  # Clear after copying

        if cached_data_snapshot:
            str_cache = f"CACHE {json.dumps(cached_data_snapshot)}"
            # print(f"LB Comms: Sending cache data: {str_cache}") # Can be verbose
            server.lb_socket.send(str_cache.encode())

            response = server.lb_socket.recv(1024).decode()  # Blocking
            if response == "ACK":
                print("LB Comms: Cache data sent successfully to LB.")
            else:
                print(f"LB Comms: Unexpected response from LB for CACHE: {response}")
                # Re-queue data if needed:
                # with server.secret_cache_lock:
                #     server.players_cached.update(cached_data_snapshot)


    except socket.timeout:
        print("LB Comms: No data received from LB for CACHE within timeout period")
        # Re-queue data if needed
    except Exception as e:
        print(f"LB Comms: Error in SendCache: {e}")
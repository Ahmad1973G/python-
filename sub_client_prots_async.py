import json
import asyncio  # Added for async operations
import sub_lb_prots_async as sub_lb_prots  # Importing the async version of LB protocols


# Helper to get writer, assuming client_id is valid and connected
# This is an internal helper for these functions if writer is not passed directly.
# However, it's cleaner if writer is passed to each function that needs it.
# For this refactor, I'll assume 'writer' is passed as an argument.

async def process_bot_damage_async(server, client_id, writer, message: str):
    try:
        messages = message.split(';')
        bot_id = int(messages[0])
        damage = int(messages[1])

        bot_died = False
        # It's better to call a method on the bot instance to handle damage
        async with server.bots_lock:  # Lock for accessing the bots dictionary
            if bot_id in server.bots:
                # The bot.take_damage method should internally handle its HP and
                # trigger server.handle_bot_death if HP <= 0.
                # server.bots[bot_id].take_damage(damage) was the new pattern.
                # For this direct adaptation of existing logic:
                target_bot = server.bots[bot_id]

        # Call the bot's own damage handling method which is async-aware
        # This method is assumed to be on the Bot object and uses server_ref to update
        if target_bot:
            bot_died = target_bot.take_damage(damage)  # This method now directly calls server.handle_bot_death

        # ACK is sent after processing
        if writer and not writer.is_closing():
            writer.write(b"ACK_DAMAGE\n")
            await writer.drain()

    except Exception as e:
        print(f"Error processing bot damage for {client_id} (Bot ID: {bot_id}): {e}")
        if writer and not writer.is_closing():
            try:
                writer.write(b"ERR_BOT_DAMAGE\n")
                await writer.drain()
            except Exception as e_send:
                print(f"Failed to send error for bot damage: {e_send}")


async def process_chat_async(server, client_id, writer, data: str):
    """Handle chat messages by routing to appropriate handler"""
    if data.startswith("SEND"):
        message_payload = data.split(" ", 1)[-1]
        await process_chat_recv_async(server, client_id, writer, message_payload)
    elif data.startswith("RECV"):
        sequence_payload = data.split(" ", 1)[-1]
        await process_chat_send_async(server, client_id, writer, sequence_payload)
    else:
        if writer and not writer.is_closing():
            writer.write(b"ERR_CHAT_FORMAT\n")
            await writer.drain()


async def process_chat_recv_async(server, client_id, writer, message: str):
    try:
        # Assuming chat_logs_lock and sequence_lock are threading.Lock for LB thread too
        # If they are purely asyncio, then server.loop.call_soon_threadsafe is not needed
        # For this structure, assume they are threading.Locks if LB also writes.
        # If only asyncio writes, they become asyncio.Lock.
        # Let's assume chat_logs and sequence_id are managed by asyncio domain here.
        async with server.chat_logs_lock:  # Make chat_logs_lock an asyncio.Lock
            server.chat_logs.append([client_id, message, server.sequence_id])
            server.sequence_id += 1

        if writer and not writer.is_closing():
            writer.write(b"ACK_CHAT_SEND\n")
            await writer.drain()
    except Exception as e:
        print(f"Error processing chat send for {client_id}: {e}")
        if writer and not writer.is_closing():
            writer.write(b"ERR_CHAT_SEND\n")
            await writer.drain()


async def process_chat_send_async(server, client_id, writer, message: str):  # Client requests new messages
    try:
        print(f"Client {client_id} requests chat messages after sequence ID: {message}")
        sequence_id_filter = int(message)

        async with server.chat_logs_lock:  # asyncio.Lock
            # Create a copy for filtering to avoid holding lock too long if logs are huge
            logs_snapshot = list(server.chat_logs)
            current_max_sequence_id = server.sequence_id - 1  # Last used sequence ID

        new_logs = [log for log in logs_snapshot if log[2] > sequence_id_filter]

        if not new_logs:
            response_data = f"UPDATED;{current_max_sequence_id}\n".encode()
        else:
            response_data = f"{current_max_sequence_id};{json.dumps(new_logs)}\n".encode()

        if writer and not writer.is_closing():
            writer.write(response_data)
            await writer.drain()

    except ValueError:
        print(f"Error processing chat request for {client_id}: Invalid sequence ID")
        if writer and not writer.is_closing():
            writer.write(b"ERR_CHAT_INVALID_SEQ\n")
            await writer.drain()
    except Exception as e:
        print(f"Error processing chat request for {client_id}: {e}")
        if writer and not writer.is_closing():
            writer.write(b"ERR_CHAT_RECV\n")
            await writer.drain()


async def process_money_async(server, client_id, writer, message: str):
    try:
        money = int(message)
        # secret_players_data is often related to login/LB state.
        # If updated by LB thread, this needs server.secret_cache_lock (threading.Lock)
        # and update via call_soon_threadsafe or make secret_players_data fully managed by asyncio.
        # Assuming for now it's an asyncio.Lock for data primarily used by game server logic.
        async with server.secret_player_data_async_lock:  # New asyncio.Lock for this
            if client_id not in server.secret_players_data:
                server.secret_players_data[client_id] = {}  # Initialize if not present
            server.secret_players_data[client_id]["PlayerMoney"] = money

        if writer and not writer.is_closing():
            writer.write(b"ACK_MONEY\n")
            await writer.drain()
    except Exception as e:
        print(f"Error processing money for {client_id}: {e}")
        # Handle error sending if needed


async def process_ammo_async(server, client_id, writer, message: str):
    try:
        ammo = int(message)
        async with server.secret_player_data_async_lock:  # New asyncio.Lock for this
            if client_id not in server.secret_players_data:
                server.secret_players_data[client_id] = {}
            server.secret_players_data[client_id]["PlayerAmmo"] = ammo  # Corrected key from original

        if writer and not writer.is_closing():
            writer.write(b"ACK_AMMO\n")
            await writer.drain()
    except Exception as e:
        print(f"Error processing ammo for {client_id}: {e}")


async def process_inventory_async(server, client_id, writer, message: str):
    try:
        items_str = message.split(';')
        items_int = [int(item) for item in items_str]  # Ensure conversion
        if len(items_int) != 5:
            raise ValueError("Inventory message must contain 5 items.")

        async with server.secret_player_data_async_lock:  # New asyncio.Lock
            if client_id not in server.secret_players_data:
                server.secret_players_data[client_id] = {}
            server.secret_players_data[client_id]["PlayerSlot1"] = items_int[0]  # Corrected keys
            server.secret_players_data[client_id]["PlayerSlot2"] = items_int[1]
            server.secret_players_data[client_id]["PlayerSlot3"] = items_int[2]
            server.secret_players_data[client_id]["PlayerSlot4"] = items_int[3]
            server.secret_players_data[client_id]["PlayerSlot5"] = items_int[4]

        if writer and not writer.is_closing():
            writer.write(b"ACK_INVENTORY\n")
            await writer.drain()
    except Exception as e:
        print(f"Error processing inventory for {client_id}: {e}")
        if writer and not writer.is_closing():
            writer.write(b"ERR_INVENTORY\n")  # Send error back
            await writer.drain()


# LOGIN and REGISTER are special: they queue data for the LB thread.
# They don't send immediate ACK to client; LB thread does after processing.
async def process_login_async(server, client_id, writer_unused, message: str):  # writer not used here
    try:
        messages = message.split(';')
        username = messages[0]
        password = messages[1]
        # waiting_login_lock is a threading.Lock, shared with LB thread
        with server.credentials_lock:  # Renamed from waiting_login_lock for clarity
            server.waiting_login[client_id] = (username, password)
        # No ACK here, client waits for LB response (sent via send_to_client_threadsafe from SortLogin)
    except Exception as e:
        print(f"Error processing login for {client_id}: {e}")
        # Optionally, send an immediate processing error if format is wrong,
        # but typically client awaits LB response for auth success/fail.


async def process_register_async(server, client_id, writer_unused, message: str):  # writer not used here
    try:
        messages = message.split(';')
        username = messages[0]
        password = messages[1]
        with server.credentials_lock:  # Renamed from waiting_register_lock
            server.waiting_register[client_id] = (username, password)
        # No ACK here
    except Exception as e:
        print(f"Error processing register for {client_id}: {e}")


async def process_move_async(server, client_id, writer, message: str):
    try:
        messages = message.split(';')
        x = int(float(messages[0]))
        y = int(float(messages[1]))
        weapon = int(float(messages[2]))  # Assuming weapon is part of move

        async with server.elements_lock:
            if client_id not in server.updated_elements: server.updated_elements[client_id] = {}
            server.updated_elements[client_id]['x'] = x
            server.updated_elements[client_id]['y'] = y
            server.updated_elements[client_id]['weapon'] = weapon

        async with server.players_data_lock:
            if client_id not in server.players_data: server.players_data[client_id] = {}  # Should be init elsewhere
            server.players_data[client_id]['x'] = x
            server.players_data[client_id]['y'] = y
            server.players_data[client_id]['weapon'] = weapon

        async with server.grid_lock:
            server.grid.add_player(client_id, x, y)

        # CheckIfMovingFULL logic (sends MOVING or ACK)
        is_moving_servers, dest_ip = server.CheckIfMoving(
            client_id)  # This is sync, reads data locked by moving_lock (threading.Lock)
        if is_moving_servers:
            if writer and not writer.is_closing():
                writer.write(f"MOVING {dest_ip}".encode())
                await writer.drain()
        else:
            if writer and not writer.is_closing():  # Send ACK if not moving to another server
                writer.write(b"ACK")
                await writer.drain()

        # CheckForLB is synchronous, updates players_to_lb (needs lb_data_lock - threading.Lock)
        # This is okay to call directly if it manages its own locks correctly for cross-thread access.
        # sub_lb_prots.CheckForLB uses self.lb_lock (assumed to be server.lb_data_lock for players_to_lb)
        sub_lb_prots.CheckForLB(server, client_id, x, y)

        # Trigger bots near player
        await server.trigger_bots_near_player(x, y, client_id)

    except Exception as e:
        print(f"Error processing move for {client_id}: {e}")
        if writer and not writer.is_closing():
            writer.write(b"ERR_MOVE\n")
            await writer.drain()


async def process_boom_async(server, client_id, writer, message: str):
    try:
        parts = message.split(";")
        x_str, y_str, Brange_str = parts[0], parts[1], parts[2]
        # Validate data if necessary (e.g., ensure they are numbers)
        async with server.elements_lock:
            if client_id not in server.updated_elements: server.updated_elements[client_id] = {}
            server.updated_elements[client_id]['explode'] = [x_str, y_str, Brange_str]
        print(f"SERVER: got bomb activation from {client_id}")
        if writer and not writer.is_closing():
            writer.write(b"ACK")
            await writer.drain()
    except Exception as e:
        print(f"SERVER: Error processing bomb for {client_id}: {e}")
        # Error handling for client


async def process_shoot_async(server, client_id, writer, message: str):
    try:
        messages = message.split(';')
        start_x, start_y, end_x, end_y, weapon = messages[0], messages[1], messages[2], messages[3], messages[4]
        # Further validation might be needed
        async with server.elements_lock:
            if client_id not in server.updated_elements: server.updated_elements[client_id] = {}
            server.updated_elements[client_id]['shoot'] = [start_x, start_y, end_x, end_y, weapon]

        if writer and not writer.is_closing():
            writer.write(b"ACK")
            await writer.drain()
    except Exception as e:
        print(f"Error processing shoot for {client_id}: {e}")


async def process_damage_taken_async(server, client_id, writer, message: str):  # Player reports their own damage
    try:
        health = int(message)  # Validate health value
        async with server.elements_lock, server.players_data_lock:
            if client_id not in server.updated_elements: server.updated_elements[client_id] = {}
            if client_id not in server.players_data: server.players_data[client_id] = {}  # Should be init

            server.updated_elements[client_id]['health'] = health
            server.players_data[client_id]['health'] = health

            if health <= 0:
                # Handle player death (e.g., mark as dead, schedule respawn, notify others)
                server.updated_elements[client_id]['dead_player'] = True  # Example
                print(f"Player {client_id} reported death.")
                # server.loop.create_task(server.handle_player_death(client_id)) # If exists

        if writer and not writer.is_closing():
            writer.write(b"ACK")
            await writer.drain()
    except Exception as e:
        print(f"Error processing damage taken for {client_id}: {e}")


async def process_power_async(server, client_id, writer, message: str):
    try:
        power_params = message.split(';')  # Assuming power is more than one param
        # Get player's current position for power activation context
        async with server.players_data_lock:  # Ensure reading player data is safe
            player_x = server.players_data.get(client_id, {}).get('x', 0)
            player_y = server.players_data.get(client_id, {}).get('y', 0)

        async with server.elements_lock:
            if client_id not in server.updated_elements: server.updated_elements[client_id] = {}
            # Original: self.updated_elements[client_id]['power'] = power, self.players_data['x'], self.players_data['y']
            # This seems to fetch global players_data x,y not specific client's. Corrected:
            server.updated_elements[client_id]['power'] = [power_params, player_x, player_y]

        if writer and not writer.is_closing():
            writer.write(b"ACK")
            await writer.drain()
    except Exception as e:
        print(f"Error processing power for {client_id}: {e}")


async def process_angle_async(server, client_id, writer, message: str):
    try:
        angle = float(message)
        async with server.elements_lock:
            if client_id not in server.updated_elements: server.updated_elements[client_id] = {}
            server.updated_elements[client_id]['angle'] = angle
        async with server.players_data_lock:
            if client_id not in server.players_data: server.players_data[client_id] = {}  # Should be init
            server.players_data[client_id]['angle'] = angle

        if writer and not writer.is_closing():
            writer.write(b"ACK")
            await writer.drain()
    except Exception as e:
        print(f"Error processing angle for {client_id}: {e}")


async def process_request_async(server, client_id, writer):  # Client requests nearby updates
    # This function returns 0 or 1 in original, used by handle_client loop.
    # The async version should just perform actions and return normally.
    # Kick logic can be handled by raising a specific exception if needed.
    try:
        # Counter logic (assuming counter_lock is asyncio.Lock or handled in server method)
        # For simplicity, direct access if it's an asyncio.Lock
        async with server.counter_lock:  # Make counter_lock an asyncio.Lock
            server.players_counter[client_id] = server.players_counter.get(client_id, 0) + 1
            counter = server.players_counter[client_id]

        if counter == 10000:  # Rate limiting example
            if writer and not writer.is_closing():
                writer.write(b"WARNING")
                await writer.drain()
        elif counter >= 100000:  # Kick for excessive requests
            if writer and not writer.is_closing():
                writer.write(b"KICK")
                await writer.drain()
            # To signal kick, could close writer or raise custom exception
            if writer and not writer.is_closing(): writer.close(); await writer.wait_closed()
            print(f"Kicking client {client_id} due to rate limit.")
            return  # End processing for this client effectively

        player_x, player_y = 0, 0
        async with server.players_data_lock:
            if client_id in server.players_data:
                player_x = server.players_data[client_id].get('x', 0)
                player_y = server.players_data[client_id].get('y', 0)
            else:  # Player data not found, critical issue or disconnected
                print(f"Request from {client_id} but player_data not found.")
                return

        async with server.grid_lock:
            nearby_ids = server.grid.get_nearby_players(player_x, player_y, 5000)  # RADIUS
            if client_id in nearby_ids:  # Client should not get its own full update here unless intended
                nearby_ids.remove(client_id)

        # print(f"Client {client_id} at ({player_x},{player_y}), nearby IDs: {nearby_ids}")

        nearby_updates_for_client = {}
        async with server.elements_lock:  # For reading updated_elements
            for pid in nearby_ids:
                if pid in server.updated_elements:
                    nearby_updates_for_client[pid] = server.updated_elements[pid]

        with server.lb_data_lock:  # Assuming other_server_lock is a threading.Lock
            nearby_updates_for_client.update(server.different_server_players)  # This might overwrite local if IDs clash

        response_str = json.dumps(nearby_updates_for_client)
        if writer and not writer.is_closing():
            writer.write(response_str.encode())
            await writer.drain()

    except KeyError as e:
        print(f"KeyError processing request for {client_id}: {e}")
        if writer and not writer.is_closing():
            writer.write(b"ERR_REQUEST")
            await writer.drain()
        return

    except ConnectionResetError:  # Or other asyncio specific connection errors
        print(f"Connection lost with {client_id} during request processing.")
    except Exception as e:
        print(f"Error processing request for {client_id}: {e}")
        if writer and not writer.is_closing():
            writer.write(b"ERR_REQUEST")
            await writer.drain()
        return

    # Include data from other servers (this data is from LB thread, needs thread-safe access)



# import traceback
# traceback.print_exc()

async def process_requestFull_async(server, client_id, writer):  # Client requests all player data
    try:
        async with server.counter_lock:  # asyncio.Lock
            server.players_counter[client_id] = server.players_counter.get(client_id, 0) + 1
            counter = server.players_counter[client_id]

        if counter == 10000:
            if writer and not writer.is_closing():
                writer.write(b"WARNING")
                await writer.drain()
        elif counter >= 100000:
            if writer and not writer.is_closing():
                writer.write(b"KICK")
                await writer.drain()
            if writer and not writer.is_closing(): writer.close(); await writer.wait_closed()
            print(f"Kicking client {client_id} due to rate limit (requestFull).")
            return

        player_x, player_y = 0, 0
        async with server.players_data_lock:
            if client_id in server.players_data:
                player_x = server.players_data[client_id].get('x', 0)
                player_y = server.players_data[client_id].get('y', 0)
            else:  # Player data not found, critical issue or disconnected
                print(f"Request from {client_id} but player_data not found.")
                return

        async with server.grid_lock:
            nearby_ids = server.grid.get_nearby_players(player_x, player_y, 5000)  # RADIUS
            if client_id in nearby_ids:  # Client should not get its own full update here unless intended
                nearby_ids.remove(client_id)

        # print(f"Client {client_id} at ({player_x},{player_y}), nearby IDs: {nearby_ids}")

        nearby_updates_for_client = {}
        async with server.elements_lock:  # For reading updated_elements
            for pid in nearby_ids:
                if pid in server.updated_elements:
                    nearby_updates_for_client[pid] = server.players_data[pid]

        # Note: This sends potentially large amounts of data. Consider if this is really needed.
        # The original also included self.different_server_players. This might be redundant
        # if players_data is the single source of truth for all known players on this server.
        # If different_server_players represents players ONLY on other servers, then merge carefully.

        response_str = json.dumps(nearby_updates_for_client)
        if writer and not writer.is_closing():
            writer.write(response_str.encode())
            await writer.drain()

    except ConnectionResetError:
        print(f"Connection lost with {client_id} during requestFull processing.")
    except Exception as e:
        print(f"Error processing requestFull for {client_id}: {e}")
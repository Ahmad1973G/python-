async def process_bot_damage(self, client_id: int, message: str, writer):
    try:
        messages = message.split(';')
        bot_id = int(messages[0])
        damage = int(messages[1])

        async with self.bots_lock:
            self.bots[bot_id].health -= damage

        if self.bots[bot_id].health <= 0:
            async with self.players_data_lock:
                bot_x = self.players_data[bot_id]['x']
                bot_y = self.players_data[bot_id]['y']

            async with self.elements_lock:
                self.updated_elements[bot_id]['dead_bot'] = {'x': bot_x, 'y': bot_y}
                self.updated_elements[bot_id]['health'] = 0

            async with self.players_data_lock:
                self.players_data[bot_id]['health'] = 0

            # Create task for bot respawn instead of thread
            asyncio.create_task(self.restart_bot(bot_id))
        else:
            async with self.elements_lock:
                self.updated_elements[bot_id]['health'] = self.bots[bot_id].health
            async with self.players_data_lock:
                self.players_data[bot_id]['health'] = self.bots[bot_id].health

        writer.write("ACK".encode())
        await writer.drain()
    except Exception as e:
        print(f"Error processing bot damage for {client_id}: {e}")


async def process_move(self, client_id: int, message: str, writer):
    try:
        messages = message.split(';')
        x = int(float(messages[0]))
        y = int(float(messages[1]))
        weapon = int(float(messages[2]))

        async with self.elements_lock:
            self.updated_elements[client_id]['x'] = x
            self.updated_elements[client_id]['y'] = y
            self.updated_elements[client_id]['weapon'] = weapon

        async with self.players_data_lock:
            self.players_data[client_id]['x'] = x
            self.players_data[client_id]['y'] = y
            self.players_data[client_id]['weapon'] = weapon

        async with self.grid_lock:
            self.grid.add_player(client_id, x, y)

        await self.CheckIfMovingFULL(client_id, writer)
        await self.CheckForLB(self, client_id, x, y)
        await self.CheckForBots(x, y)
    except Exception as e:
        print(f"Error processing move for {client_id}: {e}")


async def process_shoot(self, client_id: int, message: str, writer):
    try:
        messages = message.split(';')
        start_x = messages[0]
        start_y = messages[1]
        end_x = messages[2]
        end_y = messages[3]
        weapon = messages[4]

        async with self.elements_lock:
            self.updated_elements[client_id]['shoot'] = [start_x, start_y, end_x, end_y, weapon]

        writer.write("ACK".encode())
        await writer.drain()
    except Exception as e:
        print(f"Error processing shoot for {client_id}: {e}")


async def process_damage_taken(self, client_id: int, message: str, writer):
    try:
        health = message
        async with self.elements_lock, self.players_data_lock:
            self.updated_elements[client_id]['health'] = health
            self.players_data[client_id]['health'] = health

        writer.write("ACK".encode())
        await writer.drain()
    except Exception as e:
        print(f"Error processing damage taken for {client_id}: {e}")


async def process_power(self, client_id: int, message: str, writer):
    try:
        power = message.split(';')
        async with self.elements_lock:
            self.updated_elements[client_id]['power'] = power, self.players_data['x'], self.players_data['y']

        writer.write("ACK".encode())
        await writer.drain()
    except Exception as e:
        print(f"Error processing power for {client_id}: {e}")


async def process_angle(self, client_id: int, message: str, writer):
    try:
        angle = float(message)
        async with self.elements_lock:
            self.updated_elements[client_id]['angle'] = angle
        async with self.players_data_lock:
            self.players_data[client_id]['angle'] = angle

        writer.write("ACK".encode())
        await writer.drain()
    except Exception as e:
        print(f"Error processing angle for {client_id}: {e}")


async def process_login(self, client_id: int, message: str, writer):
    try:
        messages = message.split(';')
        username = messages[0]
        password = messages[1]
        async with self.waiting_login_lock:
            self.waiting_login[client_id] = (username, password)
    except Exception as e:
        print(f"Error processing login for {client_id}: {e}")


async def process_register(self, client_id: int, message: str, writer):
    try:
        messages = message.split(';')
        username = messages[0]
        password = messages[1]
        async with self.waiting_register_lock:
            self.waiting_register[client_id] = (username, password)
    except Exception as e:
        print(f"Error processing register for {client_id}: {e}")


async def process_Money(self, client_id: int, message: str, writer):
    try:
        money = int(message)
        async with self.secret_lock:
            self.secret_players_data[client_id]["PlayerMoney"] = money

        writer.write("ACK".encode())
        await writer.drain()
    except Exception as e:
        print(f"Error processing money for {client_id}: {e}")


async def process_Ammo(self, client_id: int, message: str, writer):
    try:
        ammo = int(message)
        async with self.secret_lock:
            self.secret_players_data[client_id]["Playerammo"] = ammo

        writer.write("ACK".encode())
        await writer.drain()
    except Exception as e:
        print(f"Error processing ammo for {client_id}: {e}")


async def process_Inventory(self, client_id: int, message: str, writer):
    try:
        items = [int(item) for item in message.split(';')]
        async with self.secret_lock:
            self.secret_players_data[client_id]["Playerslot1"] = items[0]
            self.secret_players_data[client_id]["Playerslot2"] = items[1]
            self.secret_players_data[client_id]["Playerslot3"] = items[2]
            self.secret_players_data[client_id]["Playerslot4"] = items[3]
            self.secret_players_data[client_id]["Playerslot5"] = items[4]

        writer.write("ACK".encode())
        await writer.drain()
    except Exception as e:
        print(f"Error processing inventory for {client_id}: {e}")


async def process_chat(self, client_id: int, data: str, writer):
    if data.startswith("SEND"):
        data = data.split(" ", 1)[-1]
        await process_chat_recv(self, client_id, data, writer)
    elif data.startswith("RECV"):
        data = data.split(" ", 1)[-1]
        await process_chat_send(self, client_id, data, writer)


async def process_chat_recv(self, client_id: int, message: str, writer):
    try:
        async with self.logs_lock, self.sequence_lock:
            self.chat_logs.append([client_id, message, self.sequence_id])
            self.sequence_id += 1

        writer.write("ACK".encode())
        await writer.drain()
    except Exception as e:
        print(f"Error processing chat receive for {client_id}: {e}")
        writer.write("e".encode())
        await writer.drain()


async def process_chat_send(self, client_id: int, message: str, writer):
    try:
        sequence_id = int(message)
        async with self.logs_lock:
            copy_logs = self.chat_logs.copy()

        copy_logs = [log for log in copy_logs if log[2] > sequence_id]
        if not copy_logs:
            writer.write("UPDATED".encode())
            await writer.drain()
            return

        writer.write(f"{self.sequence_id};{json.dumps(copy_logs)}".encode())
        await writer.drain()
    except ValueError:
        print(f"Error processing chat send for {client_id}: Invalid sequence ID")
        writer.write("Invalid sequence ID".encode())
        await writer.drain()
    except Exception as e:
        print(f"Error processing chat send for {client_id}: {e}")
        writer.write("e".encode())
        await writer.drain()


async def process_boom(self, client_id: int, message: str, writer):
    try:
        x, y, bomb_range = message.split(";")
        async with self.elements_lock:
            self.updated_elements[client_id]['explode'] = [x, y, bomb_range]

        print("SERVER: got bomb activation")
        writer.write("ACK".encode())
        await writer.drain()
    except Exception as e:
        print(f"SERVER: Error processing bomb for {client_id}: {e}")


async def process_request(self, client_id: int, writer):
    try:
        async with self.counter_lock:
            self.players_counter[client_id] += 1
            counter = self.players_counter[client_id]

        if counter == 10000:
            writer.write("WARNING".encode())
            await writer.drain()
            return 0
        elif counter == 100000:
            writer.write("KICK".encode())
            await writer.drain()
            writer.close()
            return 1

        async with self.grid_lock, self.players_data_lock:
            x = self.players_data[client_id]['x']
            y = self.players_data[client_id]['y']
            other_players_nearby = self.grid.get_nearby_players(x, y, 600)
            other_players_nearby.remove(client_id)

        async with self.elements_lock:
            other_players_data = {
                player_id: data
                for player_id in other_players_nearby
                if player_id in self.updated_elements and self.updated_elements[player_id]
            }
            other_players_data.update(self.different_server_players)

        writer.write(json.dumps(other_players_data).encode())
        await writer.drain()
    except Exception as e:
        print(f"Error processing request for {client_id}: {e}")
    return 0


async def process_requestFull(self, client_id: int, writer):
    try:
        async with self.counter_lock:
            self.players_counter[client_id] += 1
            counter = self.players_counter[client_id]

        if counter == 10000:
            writer.write("WARNING".encode())
            await writer.drain()
            return 0
        elif counter == 100000:
            writer.write("KICK".encode())
            await writer.drain()
            writer.close()
            return 1

        async with self.players_data_lock:
            other_players_data = {
                player_id: data
                for player_id, data in self.players_data.items()
                if data and player_id != client_id
            }

        writer.write(json.dumps(other_players_data).encode())
        await writer.drain()
    except Exception as e:
        print(f"Error processing full request for {client_id}: {e}")
    return 0
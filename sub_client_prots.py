import json
import threading

def process_bot_damage(self, client_id, message: str):
    try:
        messages = message.split(';')
        bot_id = int(messages[0])
        damage = int(messages[1])
        with self.bots_lock:
            self.bots[bot_id].health -= int(damage)
        if self.bots[bot_id].health <= 0:
           #Send dead_bot notification
            with self.players_data_lock:
                bot_x = self.players_data[bot_id]['x']
                bot_y = self.players_data[bot_id]['y']
            with self.updated_elements_lock:
                self.updated_elements[bot_id]['dead_bot'] = {'x': bot_x, 'y': bot_y}
                self.updated_elements[bot_id]['health'] = 0
            with self.players_data_lock:
                self.players_data[bot_id]['health'] = 0
            # Respawn the bot
            restart_thread = threading.Thread(target=self.restart_bot, args=(bot_id,))
            restart_thread.start()
        else:
            with self.updated_elements_lock:
                self.updated_elements[bot_id]['health'] = self.bots[bot_id].health
            with self.players_data_lock:
                self.players_data[bot_id]['health'] = self.bots[bot_id].health

        with self.clients_lock:
            self.connected_clients[client_id][1].send("ACK".encode())
    except Exception as e:
        print(f"Error processing life count for {client_id}: {e}")

def process_chat(self, client_id, data):
    """Handle chat messages by routing to appropriate handler"""
    if data.startswith("SEND"):
        data = data.split(" ", 1)[-1]
        self.process_chat_recv(self, client_id, data)
        return
    elif data.startswith("RECV"):
        data = data.split(" ", 1)[-1]
        self.process_chat_send(self, client_id, data)
        return

def process_chat_recv(self, client_id, message: str):
    try:
        with self.logs_lock and self.sequence_lock:
            self.chat_logs.append([client_id, message, self.sequence_id])
            self.sequence_id += 1
        with self.clients_lock:
            self.connected_clients[client_id][1].send("ACK".encode())
    except Exception as e:
        print(f"Error processing chat for {client_id}: {e}")
        with self.clients_lock:
            self.connected_clients[client_id][1].send("e".encode())

def process_chat_send(self, client_id, message: str):
    try:
        print("got request to send chat from client {}".format(client_id))
        sequence_id = int(message)
        with self.logs_lock:
            copy_logs = self.chat_logs.copy()

        copy_logs = [log for log in copy_logs if log[2] > sequence_id]
        if not copy_logs or copy_logs == []:
            with self.clients_lock:
                self.connected_clients[client_id][1].send("UPDATED".encode())
            del copy_logs
            return
        with self.clients_lock:
            self.connected_clients[client_id][1].send(f"{self.sequence_id};{json.dumps(copy_logs)}".encode())
        del copy_logs

    except ValueError:
        print(f"Error processing chat for {client_id}: Invalid sequence ID")
        with self.clients_lock:
            self.connected_clients[client_id][1].send("Invalid sequence ID".encode())
    except Exception as e:
        print(f"Error processing chat for {client_id}: {e}")
        with self.clients_lock:
            self.connected_clients[client_id][1].send("e".encode())

def process_Money(self, client_id, message: str):
    try:
        money = int(message)
        with self.secret_lock:
            self.secret_players_data[client_id]["PlayerMoney"] = money
        with self.clients_lock:
            self.connected_clients[client_id][1].send("ACK".encode())
    except Exception as e:
        print(f"Error processing life count for {client_id}: {e}")

def process_Ammo(self, client_id, message: str):
    try:
        ammo = int(message)
        with self.secret_lock:
            self.secret_players_data[client_id]["Playerammo"] = ammo
        with self.clients_lock:
            self.connected_clients[client_id][1].send("ACK".encode())
    except Exception as e:
        print(f"Error processing life count for {client_id}: {e}")

def process_Inventory(self, client_id, message: str):
    try:
        items = message.split(';')
        for item in items:
            item = int(item)
        with self.secret_lock:
            self.secret_players_data[client_id]["Playerslot1"] = items[0]
            self.secret_players_data[client_id]["Playerslot2"] = items[1]
            self.secret_players_data[client_id]["Playerslot3"] = items[2]
            self.secret_players_data[client_id]["Playerslot4"] = items[3]
            self.secret_players_data[client_id]["Playerslot5"] = items[4]
        with self.clients_lock:
            self.connected_clients[client_id][1].send("ACK".encode())
    except Exception as e:
        print(f"Error processing life count for {client_id}: {e}")

def process_login(self, client_id, message: str):
    try:
        messages = message.split(';')
        username = messages[0]
        password = messages[1]
        with self.waiting_login_lock:
            self.waiting_login[client_id] = (username, password)

    except Exception as e:
        print(f"Error processing login for {client_id}: {e}")


def process_register(self, client_id, message: str):
    try:
        messages = message.split(';')
        username = messages[0]
        password = messages[1]
        with self.waiting_register_lock:
            self.waiting_register[client_id] = (username, password)

    except Exception as e:
        print(f"Error processing register for {client_id}: {e}")


def process_move(self, client_id, message: str):
    try:
        messages = message.split(';')
        x = int(float(messages[0]))
        y = int(float(messages[1]))
        weapon = int(float(messages[2]))

        with self.elements_lock:
            self.updated_elements[client_id]['x'] = x
            self.updated_elements[client_id]['y'] = y
            self.updated_elements[client_id]['weapon'] = weapon
        with self.players_data_lock:
            self.players_data[client_id]['x'] = x
            self.players_data[client_id]['y'] = y
            self.players_data[client_id]['weapon'] = weapon

        with self.grid_lock:
            self.grid.add_player(client_id, x, y)
        self.CheckIfMovingFULL(client_id)
        self.CheckForLB(self, client_id, x, y)
        self.CheckForBots(x, y)
    except Exception as e:
        print(f"Error processing move for {client_id}: {e}")

def process_boom(self, client_id, message: str):
        try:
            x = message.split(";")[0]
            y = message.split(";")[1]
            Brange = message.split(";")[2]
            self.updated_elements[client_id]['explode'] = [x, y, Brange]
            print("SERVER; got bomb activation")
            self.connected_clients[client_id][1].send("ACK".encode())
        except Exception as e:
            print(f"SERVER; Error processing bomb for {client_id}: {e}")

    
def process_shoot(self, client_id, message: str):
    try:
        messages = message.split(';')
        start_x = messages[0]
        start_y = messages[1]
        end_x = messages[2]
        end_y = messages[3]
        weapon = messages[4]
        with self.elements_lock:
            self.updated_elements[client_id]['shoot'] = [start_x, start_y, end_x, end_y, weapon]
        with self.clients_lock:
            self.connected_clients[client_id][1].send("ACK".encode())
    except Exception as e:
        print(f"Error processing shoot for {client_id}: {e}")


def process_damage_taken(self, client_id, message: str):
    try:
        health = message
        with self.elements_lock and self.players_data_lock:
            self.updated_elements[client_id]['health'] = health
            self.players_data[client_id]['health'] = health
        with self.clients_lock:
            self.connected_clients[client_id][1].send("ACK".encode())
    except Exception as e:
        print(f"Error processing damage taken for {client_id}: {e}")


def process_power(self, client_id, message: str):
    try:
        power = message.split(';')
        with self.elements_lock:
            self.updated_elements[client_id]['power'] = power, self.players_data['x'], self.players_data['y']
        with self.clients_lock:
            self.connected_clients[client_id][1].send("ACK".encode())
    except Exception as e:
        print(f"Error processing power for {client_id}: {e}")


def process_angle(self, client_id, message: str):
    try:
        angle = float(message)
        with self.elements_lock:
            self.updated_elements[client_id]['angle'] = angle
        with self.players_data_lock:
            self.players_data[client_id]['angle'] = angle
        with self.clients_lock:
            self.connected_clients[client_id][1].send("ACK".encode())
    except Exception as e:
        print(f"Error processing angle for {client_id}: {e}")


def process_request(self, client_id):
    try:
        with self.counter_lock:
            self.players_counter[client_id] += 1
            counter = self.players_counter[client_id]

        if counter == 10000:
            with self.clients_lock:
                self.connected_clients[client_id][1].send("WARNING".encode())
            return 0
        elif counter == 100000:
            with self.clients_lock:
                self.connected_clients[client_id][1].send("KICK".encode())
                self.connected_clients[client_id][1].close()
            return 1

        with self.grid_lock:
            other_players_nearby = self.grid.get_nearby_players(self.players_data[client_id]['x'], self.players_data[client_id]['y'], 600)
            other_players_nearby.remove(client_id)
            print(f"other players nearby: {other_players_nearby}")
        with self.elements_lock:
            other_players_data = {}
            for player_id in other_players_nearby:
                if player_id in self.updated_elements:
                    if self.updated_elements[player_id] == {}:
                        continue
                    other_players_data[player_id] = self.updated_elements[player_id]
                else:
                    pass


        other_players_data.update(self.different_server_players)
        other_players_data_str = json.dumps(other_players_data)
        #print(other_players_data_str)
        with self.clients_lock:
            self.connected_clients[client_id][1].send(other_players_data_str.encode())
    except Exception as e:
        print(f"Error processing request for {client_id}: {e}")
    finally:
        return 0


def process_requestFull(self, client_id):
    try:
        with self.counter_lock:
            self.players_counter[client_id] += 1
            counter = self.players_counter[client_id]

        if counter == 10000:
            with self.clients_lock:
                self.connected_clients[client_id][1].send("WARNING".encode())
            return 0
        elif counter == 100000:
            with self.clients_lock:
                self.connected_clients[client_id][1].send("KICK".encode())
                self.connected_clients[client_id][1].close()
            return 1

        with self.players_data_lock:
            other_players_data = {player_id: data for player_id, data in self.players_data.items() if data != {} and player_id != client_id}

        other_players_data_str = json.dumps(other_players_data)
        print(other_players_data_str)
        with self.clients_lock:
            self.connected_clients[client_id][1].send(other_players_data_str.encode())
    except Exception as e:
        print(f"Error processing request for {client_id}: {e}")
    finally:
        return 0
import json


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
        weapon = int(messages[2])

        with self.elements_lock:
            self.updated_elements[client_id]['x'] = x
            self.updated_elements[client_id]['y'] = y
            self.updated_elements[client_id]['weapon'] = weapon
        with self.players_data_lock:
            self.players_data[client_id]['x'] = x
            self.players_data[client_id]['y'] = y
            self.players_data[client_id]['weapon'] = weapon

        self.CheckIfMovingFULL(client_id)
        self.CheckForLB(client_id, x, y)
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
        damage = message
        with self.elements_lock:
            self.updated_elements[client_id]['health'] -= damage
        with self.players_data_lock:
            self.players_data[client_id]['health'] -= damage
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

        with self.elements_lock:
            other_players_data = {player_id: data for player_id, data in self.updated_elements.items() if data != {}}

        other_players_data.update(self.different_server_players)
        other_players_data_str = json.dumps(other_players_data)
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
            other_players_data = {player_id: data for player_id, data in self.players_data.items() if data != {}}

        other_players_data_str = json.dumps(other_players_data)
        with self.clients_lock:
            self.connected_clients[client_id][1].send(other_players_data_str.encode())
    except Exception as e:
        print(f"Error processing request for {client_id}: {e}")
    finally:
        return 0
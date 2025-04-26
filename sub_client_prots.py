import json


def process_move(self, client_id, message: str):
    try:
        x = message.split(';')[0]
        y = message.split(';')[1]

        with self.elements_lock:
            self.updated_elements[client_id]['x'] = x
            self.updated_elements[client_id]['y'] = y
        with self.players_data_lock:
            self.players_data[client_id]['x'] = x
            self.players_data[client_id]['y'] = y

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
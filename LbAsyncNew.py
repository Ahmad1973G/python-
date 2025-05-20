import asyncio
import json
import random
from typing import Dict, Tuple
import database
import socket


def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


class LoadBalancerAsync:
    def __init__(self):
        self.IP = get_ip_address()
        self.PORT = 5002
        self.servers = {}  # Store connected servers (ID -> (reader, writer))
        self.servers_index = {'1': None, '2': None, '3': None, '4': None}
        self.map_width, self.map_height = 38400, 34560
        self.max_attack = 300
        self.server_borders = (self.map_width / 2, self.map_height / 2)
        self.final_packet_right = {}
        self.final_packet_to_send = {}

        self.protocols = {
            'INFO': self.process_info,
            'LOGIN': self.process_login,
            'REGISTER': self.process_register,
            'CACHE': self.process_cache,
        }

        # Locks become asyncio.Lock()

        # Initialize database connection
        self.db = database.database()

    async def init_async(self):
        self.db_lock = asyncio.Lock()
        self.right_lock = asyncio.Lock()
        self.send_lock = asyncio.Lock()

    def createSYNCpacket(self) -> bytes:
        packet = f"SYNC CODE 1, IP;{self.IP},PORT;{self.PORT}"
        return packet.encode()

    async def periodic_broadcast(self, interval=2):
        # Periodically send UDP broadcast packets to discover sub servers
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            local_addr=('0.0.0.0', 0),
            allow_broadcast=True
        )
        try:
            while True:
                transport.sendto(self.createSYNCpacket(), ('255.255.255.255', self.PORT + 1))
                print("Sent SYNC broadcast packet")
                await asyncio.sleep(interval)
        finally:
            transport.close()

    async def read_sa_send_ack(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> Tuple[bool, int]:
        try:
            data = await reader.read(1024)
            str_data = data.decode()

            if str_data == 'SYNC+ACK CODE 1':
                id = random.randint(1, 1000)
                while id in self.servers:
                    id = random.randint(1, 1000)

                for key, value in self.servers_index.items():
                    if value is None:
                        self.servers_index[key] = id
                        break

                self.servers[id] = (reader, writer)
                writer.write(f"ACK CODE 2;{id}".encode())
                await writer.drain()
                print("Received SYNC+ACK packet successfully")
                print("Sent ACK packet")
                return True, id
            return False, 0
        except Exception as e:
            print(f"Error in read_sa_send_ack: {e}")
            return False, 0

    def MoveServer(self, packet_info: Dict, server_borders: Tuple[float, float]) -> Tuple[Dict, Dict]:
        right_servers = {}
        server_to_send = {}

        for id, properties in packet_info.items():
            if properties["x"] < server_borders[0] and properties["y"] < server_borders[1]:
                right_servers[id] = self.servers_index['1']
            elif properties["x"] > server_borders[0] and properties["y"] > server_borders[1]:
                right_servers[id] = self.servers_index['3']
            elif properties["x"] < server_borders[0] and properties["y"] > server_borders[1]:
                right_servers[id] = self.servers_index['4']
            else:
                right_servers[id] = self.servers_index['2']

            self.HandlePlayerServer(id, properties, server_to_send, right_servers)

        return right_servers, server_to_send

    async def broadcast_packet(self, port: int):
        transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(
            lambda: asyncio.DatagramProtocol(),
            local_addr=('0.0.0.0', 0),
            allow_broadcast=True
        )
        transport.sendto(self.createSYNCpacket(), ('255.255.255.255', port))
        transport.close()

    def HandlePlayerServer(self, client_id, properties, server_to_send, right_servers):
        if self.server_borders[0] - self.max_attack < properties['x'] < self.server_borders[0] + self.max_attack:
            if properties['y'] < self.server_borders[1] - self.max_attack:
                server_to_send[client_id] = [self.servers_index['1'], self.servers_index['2']]
            elif properties['y'] > self.server_borders[1] + self.max_attack:
                server_to_send[client_id] = [self.servers_index['3'], self.servers_index['4']]
            else:
                server_to_send[client_id] = [self.servers_index['1'], self.servers_index['2'],
                                             self.servers_index['3'], self.servers_index['4']]
        else:
            if properties['x'] < self.server_borders[0] - self.max_attack:
                server_to_send[client_id] = [self.servers_index['1'], self.servers_index['4']]
            else:
                server_to_send[client_id] = [self.servers_index['2'], self.servers_index['3']]

        server_to_send[client_id].remove(properties['server'])

    async def start_server(self):
        server = await asyncio.start_server(
            self.handle_new_connection,
            self.IP,
            self.PORT
        )
        print(f"Load Balancer listening on {self.IP}:{self.PORT}")

        async with server:
            await server.serve_forever()

    async def handle_new_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            success, server_id = await self.read_sa_send_ack(reader, writer)
            if success:
                print(f"Server {server_id} connected")
                await self.handle_server(server_id, reader, writer)
            else:
                writer.close()
                await writer.wait_closed()
        except Exception as e:
            print(f"Error handling new connection: {e}")
            writer.close()
            await writer.wait_closed()

    async def process_info(self, data: str, server_id: int):
        try:
            data = json.loads(data)
            right_servers, server_to_send = self.MoveServer(data, self.server_borders)

            async with self.right_lock:
                for client_id, server in right_servers.items():
                    self.final_packet_right[server][client_id] = True
                    self.final_packet_right[data[client_id]['server']][client_id] = \
                        self.servers[server][1].get_extra_info('peername')[0]

            async with self.send_lock:
                for client_id, servers in server_to_send.items():
                    for server in servers:
                        self.final_packet_to_send[server] = data[client_id]

            _, writer = self.servers[server_id]
            writer.write("ACK".encode())
            await writer.drain()
        except Exception as e:
            print(f"Error processing info: {e}")

    async def process_cache(self, data: str, server_id: int):
        try:
            data = json.loads(data)
            async with self.db_lock:
                for client_id, properties in data.items():
                    properties = properties[0]
                    self.db.updateplayer(
                        properties['PlayerID'], properties['PlayerModel'],
                        properties['PlayerLifecount'], properties['PlayerMoney'],
                        properties['Playerammo'], properties['Playerslot1'],
                        properties['Playerslot2'], properties['Playerslot3'],
                        properties['Playerslot4'], properties['Playerslot5']
                    )

            _, writer = self.servers[server_id]
            writer.write("ACK".encode())
            await writer.drain()
        except Exception as e:
            print(f"Error processing cache: {e}")

    async def process_login(self, data: str, server_id: int):
        try:
            print(f"Login request from server {server_id}")
            clients = {}
            data = json.loads(data)

            async with self.db_lock:
                for client_id, (username, password) in data.items():
                    try:
                        if self.db.login(username, password):
                            player = self.db.getallplayer(username)
                            clients[client_id] = ("SUCCESS CODE LOGIN", player)
                        else:
                            clients[client_id] = ("FAILED CODE LOGIN 1", None)
                    except Exception as e:
                        print(f"Error processing login for client {client_id}: {e}")
                        clients[client_id] = (f"FAILED CODE LOGIN {e}", None)

            _, writer = self.servers[server_id]
            writer.write(json.dumps(clients).encode())
            await writer.drain()
        except Exception as e:
            print(f"Error processing login: {e}")

    async def process_register(self, data: str, server_id: int):
        try:
            clients = {}
            data = json.loads(data)

            async with self.db_lock:
                for client_id, (username, password) in data.items():
                    try:
                        if self.db.login(username, password):
                            clients[client_id] = ("FAILED CODE REGISTER 2", None)
                            continue
                        if self.db.user_exists(username):
                            clients[client_id] = ("FAILED CODE REGISTER 3", None)
                            continue

                        self.db.createplayer(1, username, password)
                        data = self.db.getallplayer(username)
                        clients[client_id] = ("SUCCESS CODE REGISTER", data)
                    except Exception as e:
                        print(f"Error processing register for client {client_id}: {e}")
                        clients[client_id] = (f"FAILED CODE REGISTER {e}", None)

            _, writer = self.servers[server_id]
            writer.write(json.dumps(clients).encode())
            await writer.drain()
        except Exception as e:
            print(f"Error processing register: {e}")

    async def handle_server(self, server_id: int, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break

                try:
                    message = data.decode()
                    if message.startswith("INDEX"):
                        for key, value in self.servers_index.items():
                            if value == server_id:
                                writer.write(f"INDEX CODE 2;{key}".encode())
                                await writer.drain()
                                break
                        continue

                    if message.startswith("BORDERS"):
                        writer.write(f"BORDERS CODE 2 {self.server_borders[0]};{self.server_borders[1]}".encode())
                        await writer.drain()
                        continue

                    protocol, *rest = message.split(maxsplit=1)
                    if protocol in self.protocols:
                        await self.protocols[protocol](rest[0] if rest else "", server_id)
                    else:
                        print(f"Unknown protocol {protocol} from server {server_id}")

                except json.JSONDecodeError as e:
                    print(f"JSON decode error from server {server_id}: {e}")
                except Exception as e:
                    print(f"Error processing message from server {server_id}: {e}")

        except ConnectionError:
            print(f"Connection lost with server {server_id}")
        except Exception as e:
            print(f"Error handling server {server_id}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            if server_id in self.servers:
                del self.servers[server_id]
            for key, value in self.servers_index.items():
                if value == server_id:
                    self.servers_index[key] = None


async def main():
    lb = LoadBalancerAsync()
    await lb.init_async()
    asyncio.create_task(lb.periodic_broadcast(5))
    await lb.start_server()


if __name__ == "__main__":
    asyncio.run(main())
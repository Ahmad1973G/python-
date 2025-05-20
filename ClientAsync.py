import asyncio
import json
from typing import Optional, Dict, Any, Tuple

class ClientProtocols:
    def __init__(self, client):
        self.client = client
        self.sequence_id = 0
        self._last_request_time = 0
        self.request_interval = 0.05  # 50ms minimum between requests

    async def send_move(self, x: float, y: float, weapon: int) -> None:
        """Send player movement update to server"""
        message = f"MOVE {x};{y};{weapon}"
        await self._send_and_wait_ack(message)

    async def send_shoot(self, start_x: float, start_y: float, end_x: float, end_y: float, weapon: int) -> None:
        """Send shooting action to server"""
        message = f"SHOOT {start_x};{start_y};{end_x};{end_y};{weapon}"
        await self._send_and_wait_ack(message)

    async def send_health_update(self, health: int) -> None:
        """Send health status update to server"""
        message = f"HEALTH {health}"
        await self._send_and_wait_ack(message)

    async def send_angle(self, angle: float) -> None:
        """Send player angle update to server"""
        message = f"ANGLE {angle}"
        await self._send_and_wait_ack(message)

    async def send_login(self, username: str, password: str) -> str:
        """Send login credentials to server and wait for response"""
        message = f"LOGIN {username};{password}"
        await self.client.writer.write(message.encode())
        await self.client.writer.drain()
        response = await self.client.reader.read(1024)
        return response.decode()

    async def send_register(self, username: str, password: str) -> str:
        """Send registration request to server and wait for response"""
        message = f"REGISTER {username};{password}"
        await self.client.writer.write(message.encode())
        await self.client.writer.drain()
        response = await self.client.reader.read(1024)
        return response.decode()

    async def send_money_update(self, amount: int) -> None:
        """Send money amount update to server"""
        message = f"MONEY {amount}"
        await self._send_and_wait_ack(message)

    async def send_ammo_update(self, amount: int) -> None:
        """Send ammo amount update to server"""
        message = f"AMMO {amount}"
        await self._send_and_wait_ack(message)

    async def send_inventory_update(self, slots: list) -> None:
        """Send inventory update to server"""
        if len(slots) != 5:
            raise ValueError("Inventory must have exactly 5 slots")
        message = f"INVENTORY {';'.join(map(str, slots))}"
        await self._send_and_wait_ack(message)

    async def send_bomb(self, x: float, y: float, bomb_range: float) -> None:
        """Send bomb placement to server"""
        message = f"BOMB {x};{y};{bomb_range}"
        await self._send_and_wait_ack(message)

    async def send_chat_message(self, message: str) -> None:
        """Send chat message to server"""
        message = f"CHAT SEND {message}"
        await self._send_and_wait_ack(message)

    async def request_chat_updates(self) -> Dict[str, Any]:
        """Request chat updates from server"""
        message = f"CHAT RECV {self.sequence_id}"
        await self.client.writer.write(message.encode())
        await self.client.writer.drain()
        response = await self.client.reader.read(1024)
        data = response.decode()
        if data == "UPDATED":
            return {}
        seq_id, messages = data.split(";", 1)
        self.sequence_id = int(seq_id)
        return json.loads(messages)

    async def send_bot_damage(self, bot_id: int, damage: int) -> None:
        """Send damage dealt to bot"""
        message = f"DAMAGE {bot_id};{damage}"
        await self._send_and_wait_ack(message)

    async def request_game_state(self) -> Dict[str, Any]:
        """Request current game state from server"""
        message = "REQUEST"
        await self.client.writer.write(message.encode())
        await self.client.writer.drain()
        response = await self.client.reader.read(4096)  # Larger buffer for game state
        data = response.decode()
        if data == "WARNING":
            print("Warning: High request frequency")
            return {}
        elif data == "KICK":
            raise ConnectionError("Kicked from server due to excessive requests")
        return json.loads(data)

    async def request_full_state(self) -> Dict[str, Any]:
        """Request full game state from server"""
        message = "REQUESTFULL"
        await self.client.writer.write(message.encode())
        await self.client.writer.drain()
        response = await self.client.reader.read(8192)  # Even larger buffer for full state
        data = response.decode()
        if data == "WARNING":
            print("Warning: High request frequency")
            return {}
        elif data == "KICK":
            raise ConnectionError("Kicked from server due to excessive requests")
        return json.loads(data)

    async def _send_and_wait_ack(self, message: str) -> None:
        """Helper method to send message and wait for ACK"""
        await self.client.writer.write(message.encode())
        await self.client.writer.drain()
        response = await self.client.reader.read(1024)
        if response.decode() != "ACK":
            raise ConnectionError(f"Server did not acknowledge message: {message}")

    async def handle_server_disconnect(self) -> None:
        """Handle server disconnection"""
        if self.client.writer:
            self.client.writer.close()
            await self.client.writer.wait_closed()
        print("Disconnected from server")
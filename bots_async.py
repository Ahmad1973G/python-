import asyncio
import math
import pygame # Assuming pygame might still be used for bot_rect, ensure it's non-blocking or handled carefully
import random  # For simplified collision response example


class Bot:
    def __init__(self, my_x, my_y, type, kd_tree, pos_to_tile, loop, bot_id, server_ref):
        self.my_x = my_x
        self.my_y = my_y
        self.hp = 150  # Initial HP
        self.shooting = False
        self.moving = False
        self.bot_id = bot_id  # For logging and server updates
        self.server_ref = server_ref  # Reference to the server instance for updates
        self.target_id = None  # Target ID, if any

        # type true= long range bot false=short
        if type:
            self.bot_range_sq = 50000  # Store squared range for efficiency
            self.bullet_speed = 150
            self.damage = 20
            self.weapon = 1
        else:
            self.bot_range_sq = 7000  # Store squared range
            self.bullet_speed = 70
            self.damage = 30
            self.weapon = 0

        self.closest_x = None
        self.closest_y = None

        self.pos_to_tile = pos_to_tile
        self.kd_tree = kd_tree
        # Assuming bot_rect is still needed, ensure its use is safe.
        # For simplicity, direct rect manipulation is kept, but in a complex GUI it might need delegation.
        # self.bot_rect = {
        #     "image": pygame.Surface((60, 60)),
        #     "rect": pygame.Rect(0, 0, 60, 60)
        # }

        self.loop = loop  # asyncio event loop
        self.async_lock = asyncio.Lock()  # For bot's internal state if accessed by multiple internal coroutines

        self.move_event = asyncio.Event()
        self.shoot_event = asyncio.Event()
        self.new_target_flag = False  # To signal re-evaluation within move loop

        self.hp = 150  # Reset HP for new bot logic

    def check_collision_nearby(self, x, y, radius=80):
        # This method is synchronous. Ensure it's fast.
        # Original collision check logic from bots.py
        # For brevity, assuming the original implementation is sound and non-blocking.
        # Simplified:
        # bot_current_rect = pygame.Rect(x - 30, y - 30, 60, 60) # Assuming 60x60 bot centered at x,y
        # center = (x, y)
        # nearby_indices = self.kd_tree.query_ball_point(center, radius)
        # for idx in nearby_indices:
        #     x_c, y_c = self.kd_tree.data[idx]
        #     coll_obj_x, coll_obj_w, coll_obj_y, coll_obj_h = self.pos_to_tile[(x_c, y_c)]
        #     coll_rect = pygame.Rect(coll_obj_x, coll_obj_y - coll_obj_h, coll_obj_w, coll_obj_h) # Adjusted y for rect
        #     if bot_current_rect.colliderect(coll_rect):
        #         return True
        # return False
        # Using the provided structure for check_collision_nearby
        # Create a temporary rect for checking
        check_rect = {"rect": pygame.Rect(0, 0, 60, 60)}  # Assuming width/height 60
        check_rect['rect'].center = (x, y)  # Center the check rect at the potential new position

        center_query_point = (x, y)  # kd-tree query point
        nearby_indices = self.kd_tree.query_ball_point(center_query_point, radius)

        for idx in nearby_indices:
            x_c, y_c = self.kd_tree.data[idx]  # These are centers of collidable tiles
            # Retrieve dimensions from pos_to_tile, original format: (obj.x, obj.width, obj.y, obj.height)
            # These seem to be top-left x, width, top-left y, height from Tiled
            tile_x, tile_w, tile_y, tile_h = self.pos_to_tile[(x_c, y_c)]

            # AABB check with tile_x, tile_y as top-left
            coll_obj_rect = pygame.Rect(tile_x, tile_y, tile_w, tile_h)
            if check_rect['rect'].colliderect(coll_obj_rect):
                return True
        return False

    def send_target(self, target_x, target_y, target_id):
        # This can be called from server (potentially different thread or async context)
        print(f"Bot {self.bot_id} received new target: ({target_x}, {target_y})")
        async def _set_event():
            if target_x is not None and target_y is not None:
                #if self.closest_x is not None and self.closest_y is not None and self.target_id is not None and self.target_id != target_id:
                #    distance = math.sqrt((self.closest_x - target_x) ** 2 + (self.closest_y - target_y) ** 2)
                #    closest_distance = math.sqrt((self.closest_x - self.my_x) ** 2 + (self.closest_y - self.my_y) ** 2)

                #   if distance > closest_distance:
                #        print(f"Bot {self.bot_id} ignoring target ({target_x}, {target_y}) as it is further than"
                #              f" current closest ({self.closest_x}, {self.closest_y})")
                #        print("Target ignored, further than current closest.")
                #        return  # Ignore this target if it's further than the current closest

                self.closest_x = target_x
                self.closest_y = target_y
                self.target_id = target_id
                self.new_target_flag = True
                self.moving = True
                self.shooting = False  # Stop shooting when a new target is assigned
                self.shoot_event.clear()
                self.move_event.set()
                print("Target set successfully.")
            else:  # No target
                self.moving = False
                self.new_target_flag = True  # To make the loop re-evaluate and stop
                self.move_event.set()  # Wake up loop to process the stop



        # bots_async.py
        self.loop.call_soon_threadsafe(asyncio.run_coroutine_threadsafe, _set_event(), self.loop)
    async def run_main_logic(self):
        # Main lifecycle coroutine for the bot
        # Starts and manages movement and shooting tasks
        await asyncio.gather(
            self.move_loop(),
            self.shoot_loop()
        )

    async def move_loop(self):  # Adapted from original move method
        while True:
            try:
                await self.move_event.wait()

                if not self.moving:
                    self.move_event.clear()
                    self.server_ref.clear_bot_data(self.bot_id)
                    continue

                self.new_target_flag = False
                await asyncio.sleep(0.1)  # Allow time for new target to be set
                # Simplified target point calculation: Bot tries to maintain bot_range from player
                # This differs from the original complex t_x, t_y calculation.
                # For a more faithful reproduction, the original math for t_x, t_y would be here.
                # The original calculation aimed to find a point t_x, t_y.
                # Let's use a simpler "move towards player until in range" or "move to maintain range"

                vec_to_player_x = self.closest_x - self.my_x
                vec_to_player_y = self.closest_y - self.my_y
                dist_sq_to_player = vec_to_player_x ** 2 + vec_to_player_y ** 2

                target_point_x, target_point_y = self.closest_x, self.closest_y  # Default: move towards player

                if dist_sq_to_player > self.bot_range_sq + 100:  # Too far, move closer
                    pass  # target_point_x,y is already player's position
                elif self.bot_range_sq - 100 > dist_sq_to_player > 0:  # Too close, move away
                    # Move to a point on the line extending from player through bot
                    dist_to_player = math.sqrt(dist_sq_to_player)
                    target_dist_from_player = math.sqrt(self.bot_range_sq)

                    target_point_x = self.closest_x - (vec_to_player_x / dist_to_player) * target_dist_from_player
                    target_point_y = self.closest_y - (vec_to_player_y / dist_to_player) * target_dist_from_player
                else:  # In range
                    self.moving = False
                    self.shooting = True
                    self.move_event.clear()
                    self.shoot_event.set()
                    print(f"Bot {self.bot_id} is in range of target ({self.closest_x}, {self.closest_y}), ready to shoot.")
                    continue

                # Inner loop for step-by-step movement towards target_point_x, target_point_y
                max_steps = 50  # Limit steps per trigger to avoid long blocks if target is far
                steps_taken = 0
                while self.moving and not self.new_target_flag and steps_taken < max_steps:
                    if abs(self.my_x - target_point_x) < 2 and abs(self.my_y - target_point_y) < 2:
                        break  # Reached intermediate target point for this cycle

                    move_dx = 0
                    if abs(self.my_x - target_point_x) >= 1:
                        move_dx = 1 if target_point_x > self.my_x else -1

                    move_dy = 0
                    if abs(self.my_y - target_point_y) >= 1:
                        move_dy = 1 if target_point_y > self.my_y else -1

                    if move_dx == 0 and move_dy == 0:  # Should be caught by distance check above
                        break

                    next_x, next_y = self.my_x + move_dx, self.my_y + move_dy

                    collided = self.check_collision_nearby(next_x, next_y)

                    if collided:
                        # Simplified collision: try to move only along one axis if the other is blocked
                        collided_x = self.check_collision_nearby(self.my_x + move_dx, self.my_y)
                        collided_y = self.check_collision_nearby(self.my_x, self.my_y + move_dy)

                        if move_dx != 0 and not collided_x:
                            self.my_x += move_dx
                        elif move_dy != 0 and not collided_y:
                            self.my_y += move_dy
                        else:
                            # Stuck for this step, perhaps try a very small random jitter next time or stop.
                            # For now, just break this inner movement attempt.
                            self.moving = False  # Stop if truly stuck
                            break
                    else:
                        self.my_x = next_x
                        self.my_y = next_y

                    self.server_ref.update_bot_data_in_server(self.bot_id, {'x': self.my_x, 'y': self.my_y})
                    await asyncio.sleep(0.05)  # Time per step
                    async with self.server_ref.players_data_lock:

                        if self.target_id not in self.server_ref.players_data:
                            print(f"Bot {self.bot_id} target ID {self.target_id} disconnected or not found.")
                            self.moving = False
                            self.closest_x = None
                            self.closest_y = None
                            self.target_id = None
                            self.shooting = False
                            self.shoot_event.clear()
                            self.server_ref.clear_bot_data(self.bot_id)
                            self.move_event.clear()
                            continue

                    steps_taken += 1

                    if self.new_target_flag: break  # New target during step-by-step

                if self.new_target_flag:  # Loop again if new target was set
                    continue

                if not self.moving:  # If movement was stopped (e.g. stuck, or reached range)
                    if abs(self.my_x - target_point_x) < 2 and abs(self.my_y - target_point_y) < 2:  # Reached
                        self.shooting = True
                        self.shoot_event.set()
                        print(f"Bot {self.bot_id} reached target ({target_point_x}, {target_point_y}), ready to shoot.")
                    self.move_event.clear()  # Stop moving until new target/event
                    self.server_ref.clear_bot_data(self.bot_id)
            except Exception as e:
                print(f"Error in move_loop for bot {self.bot_id}: {e}")
                self.moving = False
                self.shooting = False
                self.move_event.clear()
                self.shoot_event.clear()
                self.server_ref.clear_bot_data(self.bot_id)
                await asyncio.sleep(1)

    async def shoot_loop(self):
        while True:
            await self.shoot_event.wait()
            try:
                if self.shooting and self.closest_x is not None and self.closest_y is not None:
                    # Update server about shooting action
                    shoot_data = {
                        'shoot': [self.my_x, self.my_y, self.closest_x, self.closest_y, self.weapon]}
                    self.server_ref.update_bot_data_in_server(self.bot_id, shoot_data)
                    await asyncio.sleep(0.05)  # Simulate processing time for shooting
                    print(f"Bot {self.bot_id} shooting at target ({self.closest_x}, {self.closest_y})")
                    self.server_ref.clear_bot_data(self.bot_id)  # Clear bot data after shooting
                    # Simulate shooting duration / cooldown before allowing next shot trigger
                    await asyncio.sleep(1)  # Example: 0.5s cooldown or time between shots
                    async with self.server_ref.players_data_lock:
                        if self.target_id not in self.server_ref.players_data:
                            print(f"Bot {self.bot_id} target ID {self.target_id} disconnected or not found.")
                            self.shooting = False
                            self.shoot_event.clear()
                            self.server_ref.clear_bot_data(self.bot_id)
                        if self.server_ref.players_data[self.target_id]['health'] <= 0:
                            print(f"Bot {self.bot_id} target ID {self.target_id} is dead.")
                            self.shooting = False
                            self.shoot_event.clear()
                            self.server_ref.clear_bot_data(self.bot_id)
                    # If bot should continuously shoot while target is valid & in range:
                    # Check conditions again and self.shoot_event.set() if still valid.
                    # For now, one shot per trigger, then clear.
                    # To re-enable continuous shooting if conditions met:
                    dist_sq_to_player = (self.closest_x - self.my_x)**2 + (self.closest_y - self.my_y)**2
                    if self.shooting and dist_sq_to_player <= self.bot_range_sq:
                        self.shoot_event.set() # Re-trigger immediately for continuous fire
                    else:
                        self.shooting = False
                        self.shoot_event.clear()
                        self.server_ref.clear_bot_data(self.bot_id)

                else:
                    self.shooting = False
                    self.shoot_event.clear()
                    self.server_ref.clear_bot_data(self.bot_id)

            except Exception as e:
                print(f"Error in shoot_loop for bot {self.bot_id}: {e}")
                self.shooting = False
                self.shoot_event.clear()
                self.server_ref.clear_bot_data(self.bot_id)
                await asyncio.sleep(1)

    def take_damage(self, amount):
        self.hp -= amount
        self.server_ref.update_bot_data_in_server(self.bot_id, {'health': self.hp})
        if self.hp <= 0:
            self.server_ref.handle_bot_death(self.bot_id)
            return True  # Bot died
        return False  # Bot alive
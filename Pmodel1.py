import time
import pygame as pg
import json
import pytmx
from scipy.spatial import KDTree

class Player(pg.sprite.Sprite):
    
    def __init__(self, my_player, speed, weapon, power, max_health, acceleration, players, moving,
             move_offset, coins, screen, players_sprites, my_sprite, weapons, tmx_data, *groups):
        super().__init__(*groups)  # Pass groups to the Sprite initializer
        self.my_player = my_player
        self.speed = speed
        self.weapon = weapon
        self.power = power
        self.health = my_player['hp']
        self.max_health = max_health
        self.acceleration = acceleration
        self.players = players
        self.moving = moving
        self.move_offset = move_offset
        self.coins = coins
        self.screen = screen
        self.players_sprites = players_sprites
        self.my_sprite = my_sprite
        self.weapons = weapons
        self.tmx_data = tmx_data
        self.collidable_tiles = set()  # Initialize as empty set
        self.collidable_tiles = self.get_collidable_tiles(self.tmx_data)
        self.kd_tree, self.pos_to_tile = self.build_collision_kdtree(self.collidable_tiles)
        # New attributes for powerups and items
        self.invulnerability = False  # Tracks if the player is invulnerable
        self.invulnerability_end_time = None  # Time when invulnerability ends
        self.invulnerability_cooldown_end_time = 0  # Cooldown timer for invulnerability

        self.speed_power = False  # Tracks if the player has speed powerup
        self.speed_end_time = None
        self.speed_cooldown_end_time = 0  # Cooldown timer for speed powerup


        self.players_image=pg.Surface((20, 20))
        self.players_image.fill(pg.Color((255,0,0)))
        self.players_rect=self.players_image.get_rect(center=(0,0))
    
    
    def get_collidable_tiles(self, tmx_data):
        """Returns a set of tile coordinates that are collidable."""
        self.collidable_tiles = set()
        for layer in self.tmx_data.layers:
            if isinstance(layer, pytmx.TiledObjectGroup):
                if layer.name == "no walk no shoot":
                    for obj in layer:
                        # Add the coordinates of the collidable tile to the set
                        new_tile_tup = obj.x - 500, obj.width, obj.y - 330, obj.height
                        # collidable_tiles.add((obj.x // tmx_data.tilewidth, obj.y // tmx_data.tileheight))
                        self.collidable_tiles.add(new_tile_tup)
        return self.collidable_tiles


    def build_collision_kdtree(self, collidable_tiles):
        # Calculate center positions for KD-tree
        positions = [(x + w / 2, y - h / 2) for (x, w, y, h) in collidable_tiles]
        kd_tree = KDTree(positions)
        pos_to_tile = dict(zip(positions, collidable_tiles))
        return kd_tree, pos_to_tile

        
    def speed_up(self, duration):
        """Activate the speed powerup if not on cooldown."""
        current_time = time.time()
        if current_time >= self.speed_cooldown_end_time:  # Check if cooldown has expired
            self.speed_power = True
            self.original_speed = self.speed
            self.speed *= 2
            self.speed_end_time = current_time + duration
            self.speed_cooldown_end_time = self.speed_end_time + 10  # Add 10 seconds cooldown after powerup ends
            print(f"Speed powerup activated: {self.speed}")
        else:
            remaining_cooldown = int(self.speed_cooldown_end_time - current_time)
            print(f"Speed powerup is on cooldown. Try again in {remaining_cooldown} seconds.")

    def check_speed(self):
        """Check if the speed powerup period has ended."""
        if self.speed_power and time.time() > self.speed_end_time:
            self.speed_power = False
            self.speed = self.original_speed
            print("Speed powerup deactivated")

    def activate_invulnerability(self, duration):
        """Activate the invulnerability powerup if not on cooldown."""
        current_time = time.time()
        if current_time >= self.invulnerability_cooldown_end_time:  # Check if cooldown has expired
            self.invulnerability = True
            self.original_health = self.health
            self.health = 9999999  # Set health to a very high value to simulate invulnerability
            self.invulnerability_end_time = current_time + duration
            self.invulnerability_cooldown_end_time = self.invulnerability_end_time + 10  # Add 10 seconds cooldown
            print(f"Invulnerability activated: {self.health}")
        else:
            remaining_cooldown = int(self.invulnerability_cooldown_end_time - current_time)
            print(f"Invulnerability is on cooldown. Try again in {remaining_cooldown} seconds.")

    def check_invulnerability(self):
        """Check if the invulnerability period has ended."""
        if self.invulnerability and time.time() > self.invulnerability_end_time:
            self.invulnerability = False
            self.health = self.original_health
            print("Invulnerability powerup deactivated")
    
    def heal(self, amount):
        """Heal the player by a specified amount."""
        if(self.health + amount > 0):
            self.health = min(self.health + amount, self.max_health)  # Cap at max_health
        else:
            self.health = 0

    def add_ammo(self, weapon_id, amount):
        for weapon in self.weapons:
            if weapon['weapon_id'] == weapon_id:
                if (weapon['ammo'] + amount > 0):
                    weapon['ammo'] += amount
                else:
                    weapon['ammo'] = 0


    def update_players_sprites(self, players, players_sprites):
        self.players = players
        self.players_sprites = players_sprites
    
    def update_from_server(self, server_data):
        if 'powerup' in server_data and server_data['powerup'] == "invulnerability":
            self.is_invulnerable = time.time() < server_data['invulnerable_until']

    def you_dead(self):
        print('dead')


    def check_collision_nearby(self, player_rect, radius=80):
        center = (player_rect.centerx, player_rect.centery)
        nearby_indices = self.kd_tree.query_ball_point(center, radius)

        for idx in nearby_indices:
            x_c, y_c = self.kd_tree.data[idx]
            coll_obj_x, coll_obj_w, coll_obj_y, coll_obj_h = self.pos_to_tile[(x_c, y_c)]

            # AABB-style collision check (same logic as your check_collision)
            if (
                player_rect.x - player_rect.width / 2 <= coll_obj_x + coll_obj_w and
                player_rect.x + player_rect.width / 2 >= coll_obj_x and
                player_rect.y - player_rect.height / 2 <= coll_obj_y and
                player_rect.y + player_rect.height / 2 >= coll_obj_y - coll_obj_h
            ):
                #print(f"Collision with: {coll_obj_x}, {coll_obj_w}, {coll_obj_y}, {coll_obj_h}")
                return True

    #print("No collision")
        return False

    def convert_to_sprite(self, x, y, height, width, player_id):
        # Create a simple representation of the sprite
        sprite = {
            "image": pg.Surface((width, height)),
            "rect": pg.Rect(x, y, width, height),
            "id": player_id
        }
        sprite["image"].fill((255, 0, 0))  # Fill with red for visibility
        return sprite

    def convert_to_json(self):  # receives info and turns it into a json file
        client_loc = {
            "x": self.my_player['x'],
            "y": self.my_player['y'],
            "width": self.my_player['width'],
            "height": self.my_player['height'],
            "invulnerability": self.invulnerability,
            "health": self.health,
            "weapons": self.weapons
        }
        return json.dumps(client_loc)

    def print_players(self, players_sprites,bots_sprite,bots,players,angle, selected_weapon):
        PINK = (255, 174, 201)
        player_filename = ""
        # Map selected_weapon to the corresponding character image
        if selected_weapon >= 48:
            selected_weapon -= 48
        character_filename = f"char_{selected_weapon + 1}.png"

        for key, data in players_sprites.items():
            # Load and process player sprite
            if players[key]['weapon'] >= 48:
                players[key]['weapon'] -= 48
            player_filename = f"char_{players[key]['weapon'] + 1}.png"
            data['image'] = pg.image.load(player_filename).convert()
            data['image'].set_colorkey(PINK)
            data['image'] = pg.transform.rotate(data['image'], players[key]['angle'])
            data['rect'] = data['image'].get_rect(center=(data['rect'].x, data['rect'].y))

            self.screen.blit(data['image'], data['rect'])
        for key, data in bots_sprite.items():
            if 0<=data['rect'].x<=1000 and 0<=data['rect'].y<=650:
                data['image'].set_colorkey(PINK)
                data['image'] = pg.transform.rotate(data['image'], bots[key]['angle'])
                data['rect'] = data['image'].get_rect(center=(data['rect'].x, data['rect'].y))
    
                self.screen.blit(data['image'], data['rect'])
        # Draw the main player at the center
        image = pg.image.load(character_filename).convert()
        image.set_colorkey(PINK)
        image = pg.transform.rotate(image, angle)
        rect = image.get_rect(center=(500, 325))
        self.screen.blit(image, rect)
import time  # Import time for managing powerup durations
import pygame as pg
import json

class Player(pg.sprite.Sprite):
    def __init__(self, my_player, speed, weapon, power, max_health, acceleration, players, moving,
             move_offset, coins, screen, players_sprites, my_sprite, weapons, *groups):
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
        self.image = pg.Surface((my_player['width'], my_player['height']))
        self.image.fill((255, 0, 0))  # Fill with red for visibility
        self.rect = self.image.get_rect(topleft=(500, 325))  # Set initial position
        self.weapons = weapons
        # New attributes for powerups and items
        self.invulnerability = False  # Tracks if the player is invulnerable
        self.invulnerability_end_time = None  # Time when invulnerability ends

    def activate_invulnerability(self, duration):
        self.invulnerability = True
        self.original_health = self.health
        self.health = 9999999  # Set health to a very high value to simulate invulnerability
        self.invulnerability_end_time = time.time() + duration
        print("Invulnerability activated")

            
    def check_invulnerability(self):
        """Check if the invulnerability period has ended."""
        if self.invulnerability and time.time() > self.invulnerability_end_time:
            self.invulnerability = False
            self.health = self.original_health  # Restore original health

    def update(self):
        """Update player state (e.g., check if invulnerability has expired)."""
        self.check_invulnerability()


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

    def you_dead(self):
        print('dead')

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

    def print_players(self, players_sprites, screen):
        for player in players_sprites:
            player['image'].fill((255, 0, 0))
            self.screen.blit(player['image'], player['rect'])
        # Draw the main player at the center
        image = pg.Surface((20, 20))
        image.fill(pg.Color('blue'))
        rect = image.get_rect(center=(500, 325))
        self.screen.blit(image, rect)

    def move(self, players_sprites, acceleration, move_offset, moving):
        if not moving:
            return False, move_offset, self.my_player['x'], self.my_player['y']
        move_offset = (move_offset[0] * (1 - acceleration), move_offset[1] * (1 - acceleration))
        self.my_player['x'] += move_offset[0] * acceleration
        self.my_player['y'] += move_offset[1] * acceleration
        if abs(move_offset[0]) < 1 and abs(move_offset[1]) < 1:
            return False, (0, 0), self.my_player['x'], self.my_player['y']  # Stop moving when close enough
        return True, move_offset, self.my_player['x'], self.my_player['y']


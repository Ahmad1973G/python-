import time
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
        self.weapons = weapons
        # New attributes for powerups and items
        self.invulnerability = False  # Tracks if the player is invulnerable
        self.invulnerability_end_time = None  # Time when invulnerability ends
        self.speed_power = False  # Tracks if the player has speed powerup
        self.speed_end_time = None


        self.players_image=pg.Surface((20, 20))
        self.players_image.fill(pg.Color((255,0,0)))
        self.players_rect=self.players_image.get_rect(center=(0,0))
    
    def speed_up(self, duration):
        self.original_speed = self.speed
        self.speed *= 2
        self.speed_end_time = time.time() + duration
        print("Speed powerup activated")
    
    def check_speed(self):
        """Check if the speed powerup period has ended."""
        if self.speed_power and time.time() > self.speed_end_time:
            self.speed_power = False  # Reset speed powerup status
            self.speed = self.original_speed

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

    def print_players(self, players_sprites,players,angle):
        PINK = (255, 174, 201)
        for key,data in players_sprites.items():
            data['image']=pg.image.load('char.png').convert()
            data['image'].set_colorkey(PINK)
            #data['rect'].center = (data['rect'].x,data['rect'].y)

            data['image'] = pg.transform.rotate(data['image'],players[key]['angle'])
            data['rect'] = data['image'].get_rect(center=(data['rect'].x,data['rect'].y))

            self.screen.blit(data['image'],data['rect'])
        # Draw the main player at the center
        image = pg.Surface((60, 60))
        image = pg.image.load('char.png').convert()
        image.set_colorkey(PINK)

        image=pg.transform.rotate(image,angle)
        rect = image.get_rect(center=(500, 325))
        self.screen.blit(image, rect)

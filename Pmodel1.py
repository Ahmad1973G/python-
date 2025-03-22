import pygame as pg
import json

class Power:
    def __init__(self, range, damage, radius):  # This is useless for now
        self.range = range
        self.damage = damage
        self.radius = radius

    def UsePower1(self, player, duration):
        """
        SuperSpeed: Doubles the player's speed for a few seconds.
        Args:
            player (Player): The player object to apply the speed boost to.
            duration (int): The duration of the speed boost in milliseconds.
        """
        player.original_speed = player.speed
        player.speed *= 2  # Double the speed
        player.is_speed_boosted = True
        player.speed_boost_duration = duration
        player.speed_boost_start_time = pg.time.get_ticks()

    def UsePower2(self, player, duration):
        """
        Shield: Makes the player invulnerable for a few seconds
        Args:
            player (Player): The player object to apply the shield to.
            duration (int): The duration of the invulnerability in milliseconds.
        """
        player.original_health = player.health
        player.health = 9999999999  # temporary solution to invlunerablity
        player.is_shielded = True
        player.shield_duration = duration
        player.shield_start_time = pg.time.get_ticks()

    def UsePower3(self, player):
        """
        Replenish: Restores the player's health and ammo to maximum.
        Args:
            player (Player): The player object to replenish health and ammo for.
        """
        player.health = player.max_health
        player.ammo = player.max_ammo

    def UsePower4(self):
        pass

    def UsePower5(self):
        pass

class HealthKit:
    def __init__(self):
        self.name = "Health Kit"
        self.heal_amount = 25

    def use(self, player):
        player.health = min(player.health + self.heal_amount, player.max_health)
        print(f"Used {self.name}. Health: {player.health}")


class AmmoPack:
    def __init__(self):
        self.name = "Ammo Pack"
        self.ammo_amount = 50

    def use(self, player):
        player.ammo = min(player.ammo + self.ammo_amount, player.max_ammo)
        print(f"Used {self.name}. Ammo: {player.ammo}")

class Player(pg.sprite.Sprite):
    def __init__(self, my_player, speed, weapon, power, max_health, acceleration, players, moving,
                 move_offset, coins, screen, players_sprites, my_sprite, *groups):
        super().__init__(*groups)  # Pass groups to the Sprite initializer
        self.my_player = my_player
        self.speed = speed
        self.weapon = weapon
        self.power = Power(10, 20, 5)  # Initialize Power class
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
        self.max_ammo = 100  # Example max ammo
        self.ammo = self.max_ammo
        self.is_speed_boosted = False
        self.speed_boost_duration = 0
        self.speed_boost_start_time = 0
        self.is_shielded = False
        self.shield_duration = 0
        self.shield_start_time = 0

    def update(self):
        current_time = pg.time.get_ticks()

        if self.is_speed_boosted:
            if current_time - self.speed_boost_start_time >= self.speed_boost_duration:
                self.speed = self.original_speed  # Reset speed
                self.is_speed_boosted = False

        if self.is_shielded:
            if current_time - self.shield_start_time >= self.shield_duration:
                self.health = self.original_health  # Remove invulnerability
                self.is_shielded = False

    def update_players_sprites(self, players, players_sprites):
        self.players = players
        self.players_sprites = players_sprites

    def you_dead(self):
        print('dead')

    def convert_to_sprite(x, y, height, width, player_id):
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
        }
        return json.dumps(client_loc)

    def print_players(self, players_sprites, screen):
        for player in players_sprites:
            player['image'].fill((255, 0, 0))
            screen.blit(player['image'], player['rect'])

        # Draw the main player at the center
        image = pg.Surface((20, 20))
        image.fill(pg.Color('blue'))
        rect = image.get_rect(center=(500, 325))
        screen.blit(image, rect)

    def move(self, acceleration, move_offset, moving):
        if not moving:
            return False, move_offset, self.my_player['x'], self.my_player['y']

        move_offset = (move_offset[0] * (1 - acceleration), move_offset[1] * (1 - acceleration))
        added_dis1 = move_offset[0] * 0.05
        added_dis2 = move_offset[1] * 0.05
        self.my_player['x'] += added_dis1
        self.my_player['y'] += added_dis2

        if abs(move_offset[0]) < 1 and abs(move_offset[1]) < 1:
            return False, (0, 0), self.my_player['x'], self.my_player['y']  # Stop moving when close enough
        return True, move_offset, self.my_player['x'], self.my_player['y']

if __name__ == '__main__':
    pg.quit()

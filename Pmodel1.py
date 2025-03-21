import pygame as pg
import json

class Player(pg.sprite.Sprite):
    def __init__(self, my_player, speed, weapon, power,max_health, acceleration, players, moving,
                 move_offset, coins, screen, players_sprites, my_sprite, *groups):
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

    def update_players_sprites(self, players, players_sprites):
        self.players = players
        self.players_sprites = players_sprites
        
    def you_dead(self):
        print ('dead')
        
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
        added_dis1=move_offset[0] * 0.05
        added_dis2=move_offset[1] * 0.05
        self.my_player['x'] += added_dis1
        self.my_player['y'] += added_dis2
        if abs(move_offset[0]) < 1 and abs(move_offset[1]) < 1:
            return False, (0, 0), self.my_player['x'], self.my_player['y']  # Stop moving when close enough

        return True, move_offset, self.my_player['x'], self.my_player['y']


if __name__ == '__main__':
    pg.quit()
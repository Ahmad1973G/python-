import pygame as pg
import json

class Player(pg.sprite.Sprite):
    def __init__(self, x, y, height, width,player_id, speed, weapon, power, health, max_health, acceleration, players, moving, move_offset, coins,screen,players_sprites,my_sprite):
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.speed = speed
        self.weapon = weapon
        self.power = power
        self.health = health
        self.max_health = max_health
        self.acceleration = acceleration
        self.players = players
        self.moving = moving
        self.move_offset = move_offset
        self.coins = coins
        self.player_id = player_id
        self.screen = screen
        self.players_sprites = players_sprites
        self.my_sprite=my_sprite
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
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
        return json.dumps(client_loc)
    def print_players(self,players_sprites,screen):
        self.screen.fill((30, 30, 30))
        
        for player in self.players_sprites:
            player['image'].fill((255,0, 0))
            self.screen.blit(player['image'], player['rect'])
        
        # Draw the main player at the center
        image = pg.Surface((20, 20))
        image.fill(pg.Color('blue'))
        rect = image.get_rect(center=(500, 325))
        self.screen.blit(image, rect)

    
    def set_x_y(self, x, y):    # sets the x and y values of the player
        self.x = x
        self.y = y
    def move(self, players_sprites, acceleration, move_offset, moving):
        if not moving:
            return False, move_offset, self.x, self.y

        for player in players_sprites:
            player['rect'].x -= move_offset[0] * acceleration
            player['rect'].y -= move_offset[1] * acceleration

        move_offset = (move_offset[0] * (1 - acceleration), move_offset[1] * (1 - acceleration))

        if abs(move_offset[0]) < 1 and abs(move_offset[1]) < 1:
            return False, (0, 0),self.x,self.y # Stop moving when close enough

        return True, move_offset, self.x, self.y

    def colision(self, direction, players, colision_id, setup, target_pos, player_corner):
        for i in range(0, 5):
            colision_id[i] = 0
        for j in [0, 2, 4, 6]:
            direction = (325 - player_corner[j + 1] - (325 - target_pos[1])) / (player_corner[j] - 500 - (target_pos[0] - 500))
            setup = 325 - player_corner[j + 1] - direction * (player_corner[j] - 500)
            c = 0

            for player in players:
                c += 1
                for i in range(0, player.rect.width):
                    if int((player.rect.x - (player.rect.width / 2) + i - 500) * direction + setup) == int(325 - (player.rect.y + player.rect.height / 2)):
                        colision_id[c] = player.id
                for i in range(0, player.rect.width):
                    if int((player.rect.x - (player.rect.width / 2) + i - 500) * direction + setup) == int(325 - (player.rect.y - player.rect.height / 2)):
                        colision_id[c] = player.id
                for i in range(0, player.rect.height):
                    if int(((player.rect.x - player.rect.width / 2) - 500) * direction + setup) == int(325 - (player.rect.y - (player.rect.height / 2)) + i):
                        colision_id[c] = player.id
                for i in range(0, player.rect.height):
                    if int((player.rect.x + player.rect.width / 2 - 500) * direction + setup) == int(325 - (player.rect.y - player.rect.height / 2) + i):
                        colision_id[c] = player.id
        return colision_id

if __name__ == '__main__':
    pg.quit()
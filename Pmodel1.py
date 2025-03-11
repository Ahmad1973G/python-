import pygame as pg
import json

class Player(pg.sprite.Sprite):
    def __init__(self, x, y, height, width, speed, weapon, power, health, max_health, acceleration, players, moving, move_offset, coins):
        super().__init__()
        self.image = pg.Surface((width, height))
        self.image.fill(pg.Color('red'))
        self.rect = self.image.get_rect(center=(x, y))
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
        self.player_id = None
    def convert_to_sprite(self, x, y, height, width,player_id):  # receives info and turns it into a sprite
        super().__init__()
        self.image = pg.Surface((width, height))
        self.image.fill(pg.Color('red'))
        self.rect = self.image.get_rect(center=(x, y))
        self.player_id = player_id
    def convert_to_json(self):  # receives info and turns it into a json file
        client_loc = {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
        return json.dumps(client_loc)
    def print_players(players_list,players_sprites, screen):
        screen.fill((30, 30, 30))
        
        for player in players_sprites:
            screen.blit(player.image, player.rect)
        
        # Draw the main player at the center
        image = pg.Surface((20, 20))
        image.fill(pg.Color('blue'))
        rect = image.get_rect(center=(500, 325))
        screen.blit(image, rect)

    pg.display.flip()
    def set_x_y(self, x, y):    # sets the x and y values of the player
        self.x = x
        self.y = y
    def move(self, players_sprites, acceleration, move_offset, moving):
        if not moving:
            return False, move_offset, self.x, self.y

        for player in players_sprites:
            player['x'] -= move_offset[0] * acceleration
            player['y'] -= move_offset[1] * acceleration

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
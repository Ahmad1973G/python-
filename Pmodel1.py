import pygame as pg

import json


class Player:
    def _init_(self, x,y, height, width, speed, Weapon, Power, health, maxHealth,acceleration,players,moving,move_offset):
        self.x = x
        self.y = y 
        self.height = height
        self.width = width
        self.speed = speed
        self.Weapon = Weapon
        self.Power = Power
        self.health = health
        self.maxHealth = maxHealth
        self.acceleration=acceleration
        self.players=players
        self.moving=moving
        self.move_offset = (0, 0)
        
        
    def convert_to_json(self):  # receives info and turns it into a json file 
        client_loc = {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
        return json.dumps(client_loc)
        
    def move(self, players, acceleration, move_offset, moving):
        if not moving:
            return False, move_offset

        
        for player in players:
            player['x'] -= move_offset[0] * acceleration
            player['y'] -= move_offset[1] * acceleration
        
        move_offset = (move_offset[0]*(1-acceleration), move_offset[1]*(1-acceleration))
        
        if abs(move_offset[0]) < 1 and abs(move_offset[1]) < 1:
            return False, (0, 0)  # Stop moving when close enough
        
        return True, move_offset


    def colision (self, mouse_pos):
        if self.startX_col <= self.x <= self.endX_col:
            if mouse_pos[1] > self.y:
                if self.startY_col <= self.y + 20 <= self.endY_col:
                    self.rise = 0
                    self.run = 0
            elif mouse_pos[1] < self.y:
                if self.startY_col <= self.y - 20 <= self.endY_col:
                    self.rise = 0
                    self.run = 0

        elif self.startY_col <= self.y <= self.endY_col:
            if mouse_pos[0] > self.x:
                if self.startX_col <= self.x + 20 <= self.endX_col:
                    self.run = 0
                    self.rise = 0
            elif mouse_pos[0] < self.x:
                if self.startX_col <= self.x - 20 <= self.endX_col:
                    self.run = 0
                    self.rise = 0

    if __name__ == '__main__':
        pg.quit()
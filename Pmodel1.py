import pygame as pg

import json


class Player:
    def _init_(self, x,diff, y, hight, width, speed, Weapon, Power, health, maxHealth,acceleration,client_loc):
        self.x = x
        self.diff=diff
        self.Weapon = Weapon
        self.Power = Power
        self.y = y
        self.hight = hight
        self.width = width
        self.speed = speed
        self.health = health
        self.maxHealth = maxHealth
        self.acceleration=acceleration
        self.client_loc=client_loc
        
        
    def convert_to_json(self, x, y, width, height, id):  # receives info and turns it into a json file
        client_loc = {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "id": id

        }
        with open('move_data.json', 'w') as json_file:
            json.dump(client_loc, json_file)
            
        return client_loc
    def move(self,x, y,diff, client_loc, acceleration):
        while True:
            for event in pg.event.get():
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    return
            self.client_loc['x'] = (diff[0]) * self.acceleration
            self.client_loc['y'] = (diff[1]) * self.acceleration

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
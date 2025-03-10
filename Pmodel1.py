
import pygame as pg

import json


class Player:
    def __init__(self, x, y, hight, width, speed, Weapon, Power, health, maxHealth,acceleration):
        self.x = x
        self.Weapon = Weapon
        self.Power = Power
        self.y = y
        self.hight = hight
        self.width = width
        self.speed = speed
        self.health = health
        self.maxHealth = maxHealth
        self.acceleration=acceleration
        
        
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



    
    





        
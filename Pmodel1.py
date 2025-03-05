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
    def colision(self,direction,players,colision_id,setup,target_pos,player_corner):
        for i in range(0,5):
            colision_id[i]=0
        for j in [0,2,4,6]:
            direction=(325-player_corner[j+1]-(325-target_pos[1]))/(player_corner[j]-500-(target_pos[0]-500))
            setup=325-player_corner[j+1]-direction*(player_corner[j]-500)
            c=0

            for player in players:
                c+=1
                for i in range(0,player['width']):
                    if int((player['x']-(player['width']/2)+i-500)*direction+setup)==int(325-(player['y']+player['height']/2)):
                        colision_id[c]=player['id']
                for i in range(0,player['width']):
                    if int((player['x']-(player['width']/2)+i-500)*direction+setup)==int(325-(player['y']-player['height']/2)):
                        colision_id[c]=player['id']
                for i in range(0,player['height']):
                    if int(((player['x']-player['width']/2)-500)*direction+setup)==int(325-(player['y']-(player['height']/2))+i):
                        colision_id[c]=player['id'] 
                for i in range(0,player['height']):
                    if int((player['x']+player['width']/2-500)*direction+setup)==int(325-(player['y']-player['height']/2)+i):
                        colision_id[c]=player['id']
        return colision_id


    if __name__ == '_main_':
        pg.quit()
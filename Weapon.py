import pygame
import time
import database
players = database.database()


class Weapon:
    def __init__(self,weapons):
        self.weapons=weapons
    
    def shoot(self, players):
        if players.getplayerammo() > 0:
            players.updateplayerammo(players.getplayerammo()-1)
            checkhit()
            time.sleep()


    def reload(self, players):
        if players.getplayerammo() < 00:
            players.updateplayerammo(100)
            time.sleep(players.getplayermodel()[2])

    def checkhit(self):
        pass
import pygame
import database
players = database.database()

class Inventory:
    def __init__(self, money=players.getplayermoney, slots=players.getplayerslots, ammo=players.getplayerammo):
        self.money = money
        self.slots = slots
        self.ammo = ammo

    def dropitem(self, slots, index, players):
        self.slots[index] = None
        return self.slots
    
    def pickupitem(self, item):
        for i in range(5):
            if self.slots[i] is None:
                self.slots[i] = item
                return self.slots
        print("You don't have enough space")
        return self.slots
    
    def buy(self, cost, wanteditem):
        if self.money >= cost:
            self.money -= cost
            self.pickupitem(wanteditem)
        else:
            print("You don't have enough money")
        return self.money, self.slots
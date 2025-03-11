import pygame

class Inventory:
    def __init__(self, gold=0, slots=None, ammo=0):
        if slots is None:
            slots = [None] * 5
        self.gold = gold
        self.slots = slots
        self.ammo = ammo

    def dropitem(self, index):
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
        if self.gold >= cost:
            self.gold -= cost
            self.pickupitem(wanteditem)
        else:
            print("You don't have enough gold")
        return self.gold, self.slots
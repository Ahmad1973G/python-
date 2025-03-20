import pygame

class Inventory:
    def __init__(self, gold=0, slots=None, ammo=0):
        if slots is None:
            slots = [None] * 5
        self.gold = gold
        self.slots = slots
        self.ammo = ammo

<<<<<<< HEAD

    def dropitem(slots, index):

        
        slots [index] = null

        return slots
    
    def pickupitem(slots, item):
        for i in range(0, 5):
            if slots[i] == null:
                slots[i] = item
                return slots

        return slots
    
    def buy(self, gold, slots, cost, wanteditem):
        if gold >= cost:
            gold -= cost
            pickupitem(slots, wanteditem)
=======
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
>>>>>>> b59e435e9847ed542dc1cad5e47c5b65495a0274
        else:
            print("You don't have enough gold")
        return self.gold, self.slots
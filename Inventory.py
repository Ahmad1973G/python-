import pygame

class Inventory:


    def __init__(self, gold = 0, slots = []*5, ammo = 0):
        self.gold = gold
        self.slot1 = slots
        self.ammo = ammo


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
        else:
            print("you dont have enough gold")


        return gold, slots
    
    
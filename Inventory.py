import pygame

class Inventory:


    def __init__(self, gold = 0, slots = []*5, ammo = 0):
        self.gold = gold
        self.slot1 = slots
        self.ammo = ammo


    def dropitem(self, slots, index):
        slots [index]=1
        

        return slots
    
    def pickupitem(self, slots, item):
        for i in range(0, 5):
            if slots[i] != None:
                slots[i] = item
                return slots
        print("you dont have enough space")

        return slots
    
    def buy(self, gold, slots, cost, wanteditem):
        if gold >= cost:
            gold -= cost
            pickupitem(self, slots, wanteditem)
        else:
            print("you dont have enough gold")


        return gold, slots
    
    
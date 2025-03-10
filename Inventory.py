import pygame

class Inventory:


    def __init__(self, gold = 0, slots = []*5, ammo = 0):
        self.gold = gold
        self.slots = slots
        self.ammo = ammo


    def dropitem(self, slots, index):
        self.slots [index]=1 #self.slot1[index] = None
        

        return slots
    
    def pickupitem(self, slots, item):
        for i in range(0, 5):
            if slots[i] != null: #None
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
    
    
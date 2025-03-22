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

    def use_item(self, index, player):
        """
        Uses the item at the specified inventory index.

        Args:
            index (int): The index of the item in the inventory.
            player (Player): The player object using the item.
        """
        item = self.slots[index]
        if item:
            if item == "Health Potion":
                player.health = min(player.health + 50, player.max_health)  # Restore 50 health, but not over max
                print("Used Health Potion. Health:", player.health)
            elif item == "Ammo Pack":
                player.ammo = player.max_ammo  # Replenish ammo
                print("Used Ammo Pack. Ammo:", player.ammo)
            elif item == "Grenade":
                print("Grenade is not implemented yet")
                pass
            elif item == "Invisibility Cloak":
                player.is_invisible = True
                player.invisibility_duration = 5000  # 5 seconds
                player.invisibility_start_time = pygame.time.get_ticks()
                print("Used Invisibility Cloak. Invisible for 5 seconds.")
            self.slots[index] = None  # Remove item after use
        else:
            print("No item in that slot.")

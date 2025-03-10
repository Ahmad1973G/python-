import pygame
import time

class Weapon:

    def __init__(self, range, damage, c_ammo, hitDelay, RD, maxAmmo, ammo):
        self.range = range
        self.damage = damage
        self.maxAmmo = maxAmmo
        self.hitDelay = hitDelay
        self.RD = RD
        self.ammo = ammo
        self.c_ammo = c_ammo

    def reload(ammo, RD, maxAmmo):
        if c_ammo < maxAmmo:
            ammo -= maxAmmo - c_ammo
            c_ammo = maxAmmo
            time. sleep(RD)
        return c_ammo, ammo

    
    def hit(range, damage, ammo, hitDlelay):
        ammo -= 1
        checkhit(range)
        time.sleep(hitDelay)
        return ammo

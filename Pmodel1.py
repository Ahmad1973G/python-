import pygame
import pygame as pg

import json


class Player:
    def __init__(self, x, y, hight, width, speed, Weapon, Power, health, maxHealth,acceleration):
        self.x = x
        self.Weapon = Weapon
        self.Power = Power
        self.y = y
        self.hight = hight
        self.width = width
        self.speed = speed
        self.health = health
        self.maxHealth = maxHealth
        self.acceleration=acceleration

    def move(self):
        pg.init()
        LEFT = 1
        RED = (0, 0, 0)
        GRAY = (148, 153, 157)
        screen = pg.display.set_mode((640, 480))
        clock = pg.time.Clock()
        image = pg.Surface((30, 30))
        image.fill(pg.Color('dodgerblue1'))
        rect = image.get_rect(center=(self.x, self.y))  # Blit position.

        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return

            mouse_pos = pg.mouse.get_pos()
            # x and y distances to the target.
            self.run = (mouse_pos[0] - self.x) * self.acceleration  # Scale it to the desired length.
            self.rise = (mouse_pos[1] - self.y) * self.acceleration
            # Update the position.

            if event.type == pg.MOUSEBUTTONDOWN\
                    and event.button == LEFT:
                self.x += self.run
                self.y += self.rise
                rect.center = self.x, self.y

            screen.fill((0, 0, 0))
            screen.blit(pg.image.load('niggers.png').convert(), (0, 0))
            screen.blit(image, rect)
            pg.display.flip()
            clock.tick(60)

    def colision (self, mouse_pos):
        if self.startX_col <= self.x <= self.endX_col:
            if mouse_pos[1] > self.y:
                if self.startY_col <= self.y + 20 <= self.endY_col:
                    self.rise = 0
                    self.run = 0
            elif mouse_pos[1] < self.y:
                if self.startY_col <= self.y - 20 <= self.endY_col:
                    self.rise = 0
                    self.run = 0

        elif self.startY_col <= self.y <= self.endY_col:
            if mouse_pos[0] > self.x:
                if self.startX_col <= self.x + 20 <= self.endX_col:
                    self.run = 0
                    self.rise = 0
            elif mouse_pos[0] < self.x:
                if self.startX_col <= self.x - 20 <= self.endX_col:
                    self.run = 0
                    self.rise = 0

    if __name__ == '__main__':
        move()
        pg.quit()



    
    





        
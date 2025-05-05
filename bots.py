import time
from fileinput import close

import ClientSocket
import pygame
import math
import threading


class Bots ():
    def __init__(self,my_x,my_y,type,closest_x,closest_y,screen):
        #type true= long range bot false=short
        #closest_p=0 if no player is close
        self.my_x=my_x
        self.my_y=my_y
        self.hp=150
        self.moving=True
        self.bot_rect={
            "image": pygame.Surface((60, 60)),
            "rect": pygame.Rect(500, 325, 60, 60)
        }
        if type:
            self.bot_range=50000
            self.bullet_speed=150
            self.damage=20
            self.weapon=1
        else:
            self.bot_range = 7000
            self.bullet_speed =70
            self.damage = 30
            self.weapon=0
        self.screen=screen
        self.closest_x=closest_x
        self.Socket = ClientSocket.ClientServer()
        self.closest_y=closest_y
        self.lock=threading.Lock()
        self.new_target=False
        self.thread_movebots=threading.Thread(target=self.move)
        self.thread_movebots.start()

    def SeNdTArGeT(self,x,y):
        self.closest_y=y
        self.closest_x=x
        self.new_target=True
        self.moving=True
    def move(self):
        target_x=False
        target_y=False
        while True:
            if self.moving:
                self.new_target=False
                col=False
                t_x = self.closest_x - 500
                t_y = 325 - self.closest_y
                m_x = self.my_x - 500 - t_x
                m_y =  325-t_y- self.my_y
                if m_x==0:
                    m_x=1
                direction = m_y / m_x
                t_x = (m_x / abs(m_x)) * math.sqrt(self.bot_range / (direction * direction + 1))
                t_y = self.closest_y - direction * t_x
                t_x += self.closest_x
                hypo_x=self.my_x
                hypo_y=self.my_y
                while not self.new_target and (not target_x or not target_y):
                    if int(self.my_x)!=int(t_x):
                        move_x=(t_x-self.my_x)/abs(t_x-self.my_x)
                    else:
                        target_x=True
                    if int(self.my_y) != int(t_y):
                        move_y=(t_y-self.my_y)/abs(t_y-self.my_y)
                    else:
                        target_y=True
                    self.my_x+=move_x
                    self.my_y+=move_y
                    self.bot_rect['rect'].x=self.my_x
                    self.bot_rect['rect'].y=self.my_y
                    self.bot_rect['image']=pygame.Surface((30, 30))
                    self.bot_rect['image'].fill((255, 0, 0))
                    self.screen.fill((0, 0, 0))
                    self.screen.blit(self.bot_rect['image'], self.bot_rect['rect'])
                    pygame.display.flip()
                    time.sleep(0.001)
                    if col:
                        optiona_x = self.my_x
                        optiona_y = self.my_y
                        optionb_x = self.my_x
                        optionb_y = self.my_y
                        if move_y==0:
                            move_y=-move_x
                            move_x=0
                        else:

                            optionb_y += move_y
                            if move_x==0:
                                move_x=5

                            optiona_x+=move_x
                        while True:
                            if not col:#option a
                                break
                            if not col:#option b
                                break
                            optionb_y += move_y
                            optiona_x += move_x
                if target_x and target_y:
                    self.moving=False
            elif target_x and target_y:
                time.sleep(0.5)
                self.Socket.sendSHOOT(self.my_x,self.my_y,self.closest_x,self.closest_y,self.weapon)
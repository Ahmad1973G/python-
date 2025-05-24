import time
import ClientSocket
import pygame
import math
import threading


class Bot:
    def __init__(self,my_x,my_y,type,closest_x,closest_y,kd_tree,pos_to_tile):
        #type true= long range bot false=short
        #closest_p=0 if no player is close
        self.my_x=my_x
        self.my_y=my_y
        self.hp=150
        self.shooting=False
        self.moving= False
        self.bot_rect={
            "image": pygame.Surface((60, 60)),
            "rect": pygame.Rect(0,0, 60, 60)
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
        self.closest_x=closest_x
        self.Socket = ClientSocket.ClientServer()
        self.closest_y=closest_y
        self.pos_to_tile=pos_to_tile
        self.kd_tree= kd_tree
        self.lock=threading.Lock()
        self.new_target=False
        self.thread_movebots=threading.Thread(target=self.move)
        self.thread_movebots.start()

    def check_collision_nearby(self,x,y, radius=80):
        self.bot_rect['rect'].x=x
        self.bot_rect['rect'].y=y
        center = (self.bot_rect['rect'].x, self.bot_rect['rect'].y)
        nearby_indices = self.kd_tree.query_ball_point(center, radius)

        for idx in nearby_indices:
            x_c, y_c = self.kd_tree.data[idx]
            coll_obj_x, coll_obj_w, coll_obj_y, coll_obj_h = self.pos_to_tile[(x_c, y_c)]

            # AABB-style collision check (same logic as your check_collision)
            if (
                    self.bot_rect['rect'].x - self.bot_rect['rect'].width / 2 <= coll_obj_x + coll_obj_w and
                    self.bot_rect['rect'].x + self.bot_rect['rect'].width / 2 >= coll_obj_x and
                    self.bot_rect['rect'].y - self.bot_rect['rect'].height / 2 <= coll_obj_y and
                    self.bot_rect['rect'].y + self.bot_rect['rect'].height / 2 >= coll_obj_y - coll_obj_h
            ):
                # print(f"Collision with: {coll_obj_x}, {coll_obj_w}, {coll_obj_y}, {coll_obj_h}")
                return True

        # print("No collision")
        return False
    def SeNdTArGeT(self,x,y):
        if x is not None and y is not None:
            self.closest_y=y
            self.closest_x=x
            self.new_target=True
            self.shooting=False
            self.moving=True
        else:
            self.moving=False
    def move(self):
        target_x=False
        target_y=False
        while True:
            if self.moving:
                self.new_target=False
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
                target_x = False
                target_y = False
                while not self.new_target and (not target_x or not target_y):
                    if int(self.my_x)!=int(t_x):
                        move_x=(t_x-self.my_x)/abs(t_x-self.my_x)
                    else:
                        target_x=True
                        move_x=0
                    if int(self.my_y) != int(t_y):
                        move_y=(t_y-self.my_y)/abs(t_y-self.my_y)
                    else:
                        target_y=True
                        move_y=0
                    self.my_x+=move_x
                    self.my_y+=move_y
                    time.sleep(0.1)
                    if self.check_collision_nearby(self.my_x,self.my_y):
                        option_x = [self.my_x,self.my_x]
                        option_y = [self.my_y,self.my_y]
                        if move_y==0:
                            move_y=5
                            move_x=0
                        else:

                            option_y[1] += move_y
                            if move_x==0:
                                move_x=5
                                move_y=0

                            option_x[0]+=move_x
                        while True:
                            if not self.check_collision_nearby(option_x[0],option_y[0]):
                                best_route=0
                                move_y=0
                                break

                            if not self.check_collision_nearby(option_x[1],option_y[1]):
                                best_route=1
                                move_x=0
                                break
                            option_y[1] += move_y
                            option_x[0] += move_x
                        while self.my_x!=option_x[best_route] or self.my_y!=option_y[best_route]:
                            self.my_x+=move_x
                            self.my_y+=move_y

                            time.sleep(0.1)
                if target_x and target_y:
                    self.shooting=True
                    self.moving=False
            elif target_x and target_y and not self.new_target:
                time.sleep(0.001)
                #self.Socket.sendSHOOT(self.my_x,self.my_y,self.closest_x,self.closest_y,self.weapon)
import pygame as pg
import Pmodel1 
import json
import threading
import time




def get_mouse_pos():
    mouse_pos = pg.mouse.get_pos()
    for event in pg.event.get():
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            x=mouse_pos[0]
            y=mouse_pos[1]
            diff[0]=500-x
            diff[1]=325-y
            obj.move(x, y, obj.client_loc, obj.acceleration)



    
def print_players(players_list, client_loc):
    screen = pg.display.set_mode((1000, 650))
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
        for player in players_list:
            if player['id'] != client_loc['id']:
                image = pg.Surface((player['width'], player['height']))
                image.fill(pg.Color('red'))
                rect = image.get_rect(center=(player['x']-diff[0], player['y']-diff[1]))
                screen.blit(image, rect)
                
            
        else:
            image = pg.Surface((client_loc['width'], client_loc['height']))
            image.fill(pg.Color('blue'))
            rect = image.get_rect(center=(500, 325))
            screen.blit(image, rect)
            
        pg.display.flip()
        obj.convert_to_json(300, 325,20, 20, 0)    

    
if __name__ == '__main__':
    client_loc = {"x":500, "y":325, "width": 20, "height": 20, "id": 1}  # Main player is always in the middle.
    diff=[500-client_loc['x'],325-client_loc['y']]
    players_list = [
        {"x": 600, "y": 400,'diff_x':diff[0],'diff_y':diff[1], "width": 20, "height": 20, "id": 0},
        {"x": 500, "y": 325,'diff_x':diff[0],'diff_y':diff[1], "width": 20, "height": 20, "id": 1},
        {"x": 400, "y": 300,'diff_x':diff[0],'diff_y':diff[1], "width": 20, "height": 20, "id": 2},
        {"x": 700, "y": 500,'diff_x':diff[0],'diff_y':diff[1], "width": 20, "height": 20, "id": 3}
    ]
    
    obj=Pmodel1.Player()
    #def _init_(self, x,diff, y, hight, width, speed, Weapon, Power, health, maxHealth,acceleration,client_loc)
    obj._init_(500,diff, 325, 20, 20, 5, "Gun", "Power", 100, 100, 0.1, client_loc)
    obj.convert_to_json(500, 325, 20, 20, 0)
    thread1=threading.Thread(target=print_players(players_list, client_loc))
    thread2=threading.Thread(target=get_mouse_pos)
    pg.init()
    thread2.start()
    thread1.start() 
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()
 
        
    
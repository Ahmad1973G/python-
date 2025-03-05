import pygame as pg
import json
import Pmodel1
import ClientSocket
import pygame
import math
def print_players(players_list, screen):
    screen.fill((30, 30, 30))
    
    for player in players_list:
        image = pg.Surface((player['width'], player['height']))
        image.fill(pg.Color('red'))
        rect = image.get_rect(center=(player['x'], player['y']))
        screen.blit(image, rect)
    
    # Draw the main player at the center
    image = pg.Surface((20, 20))
    image.fill(pg.Color('blue'))
    rect = image.get_rect(center=(500, 325))
    screen.blit(image, rect)

    pg.display.flip()

def run_game():
    pg.init()

    screen = pg.display.set_mode((1000, 650))
    clock = pg.time.Clock()
    players=[]
    obj=Pmodel1.Player()
#x,y, hight, width, speed, Weapon, Power, health, maxHealth,acceleration,players,moving,move_offset):
    BLACK = (0, 0, 0)
    move_offset = (0, 0)
    acceleration = 0.1
    moving = False
    colision_id=[0,0,0,0,0] #id of the player that will colide
    direction = 0 #like m in y=mx+b
    setup=0#like b in y=mx+b
    player_corner=[500-(20/2),325-(20/2),500+(20/2),325-(20/2),500-(20/2),325+(20/2),500+(20/2),325+(20/2)]
    obj.init(500, 325, 20, 20, 1, 1, 1, 100, 100, 0.1,'players','False', (500, 325),direction,colision_id,player_corner)
    Socket = ClientSocket.ClientServer()
    Socket.connect()
    players = Socket.run_conn(obj.convert_to_json())
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()

                exit()
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                target_pos = pg.mouse.get_pos()
                move_offset = (target_pos[0] - 500, target_pos[1] - 325)
                moving = True
                colision_id=obj.colision(direction,players,colision_id,setup,target_pos,player_corner)
                for j in range(colision_id._len_()):
                    if colision_id[j]!=0:
                        for i in range(colision_id._len_()):
                            if colision_id[i]==0:
                                colision_id[i]=colision_id[j]
                                colision_id[j]=0
                                break
        players = Socket.run_conn(obj.convert_to_json())
        if colision_id[0]==0:

            moving, move_offset = obj.move(players, acceleration, move_offset, moving) 
       # else:
        #    for i in range(colision_id._len_()):
         #       if colision_id[i]==0:
          #          break
           #     colision_id[i]=math.sqrt()
        print_players(players, screen)
        
        clock.tick(60)

run_game()
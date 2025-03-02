import pygame as pg
import json
import Pmodel1
import ClientSocket

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
    players = [
        {"x": 600, "y": 400, "width": 20, "height": 20, "id": 1},
        {"x": 400, "y": 300, "width": 20, "height": 20, "id": 2},
        {"x": 700, "y": 500, "width": 20, "height": 20, "id": 3}
    ]
    obj=Pmodel1.Player()
    obj._init_(500, 325, 20, 20, 1, 1, 1, 100, 100, 0.1,'players','False', (500, 325))
    move_offset = (0, 0)
    acceleration = 0.1
    moving = False
    
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()

                exit()
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                target_pos = pg.mouse.get_pos()
                move_offset = (target_pos[0] - 500, target_pos[1] - 325)
                moving = True
                
        moving, move_offset = obj.move(players, acceleration, move_offset, moving)
        print_players(players, screen)
        Socket = ClientSocket.ClientSocket()
        Socket.connect()
        players = Socket.run_conn(obj.convert_to_json())
        print_players(players, screen)
        clock.tick(60)

run_game()
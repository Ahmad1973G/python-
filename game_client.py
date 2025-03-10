import pygame as pg
import json
import Pmodel1
import ClientSocket
import pytmx
import math
import sys
import os

def load_tmx_map(filename):
    """Load TMX map file and return data."""
    if not os.path.exists(filename):
        print(f"❌ ERROR: TMX file not found: {filename}")
        return None
    try:
        return pytmx.load_pygame(filename, pixelalpha=True)
    except Exception as e:
        print(f"❌ Error loading TMX file: {e} - {sys.exc_info()}")
        return None

def draw_map(screen, tmx_data, world_offset):
    """Draw the TMX map with an offset to simulate camera movement."""
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    screen.blit(tile, (x * tmx_data.tilewidth + world_offset[0], 
                                       y * tmx_data.tileheight + world_offset[1]))

def print_players(players_list, screen, world_offset):
    for player in players_list:
        image = pg.Surface((player['width'], player['height']))
        image.fill(pg.Color('red'))
        rect = image.get_rect(center=(player['x'] + world_offset[0], player['y'] + world_offset[1]))
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
    my_player = {'x': 400, 'y': 400, 'width': 20, 'height': 20, 'id': 0}
    players = []
    obj = Pmodel1.Player(400, 400, 20, 20, 1, 1, 1, 100, 100, 0.1)
    BLACK = (0, 0, 0)
    move_offset = (0, 0)
    world_offset = (0, 0)
    tmx_data = load_tmx_map(r"c:/webroot/map.tmx")
    acceleration = 0.1
    moving = False
    colision_id = [0, 0, 0, 0, 0]  # id of the player that will collide
    direction = 0  # like m in y=mx+b
    setup = 0  # like b in y=mx+b
    x = 400
    y = 400
    player_corner = [500 - (20 / 2), 325 - (20 / 2), 500 + (20 / 2), 325 - (20 / 2), 500 - (20 / 2), 325 + (20 / 2), 500 + (20 / 2), 325 + (20 / 2)]
    obj.init(400, 400, 20, 20, 1, 1, 1, 100, 100, 0.1)
    Socket = ClientSocket.ClientServer()
    Socket.connect()
    players = Socket.run_conn(obj.convert_to_json())
    
    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                target_pos = pg.mouse.get_pos()
                move_offset = (target_pos[0] - 500, target_pos[1] - 325)
                moving = True
                colision_id = obj.colision(direction, players, colision_id, setup, target_pos, player_corner)
                for j in range(len(colision_id)):
                    if colision_id[j] != 0:
                        for i in range(len(colision_id)):
                            if colision_id[i] == 0:
                                colision_id[i] = colision_id[j]
                                colision_id[j] = 0
                                break
        
        players = Socket.run_conn(obj.convert_to_json())
        if colision_id[0] == 0:
            moving, move_offset, x, y = obj.move(players, acceleration, move_offset, moving)
            Socket.send(json.dumps({'x': x, 'y': y}))
        
        world_offset = (500 - x, 325 - y)
        screen.fill(BLACK)
        draw_map(screen, tmx_data, world_offset)
        print_players(players, screen, world_offset)
        
        clock.tick(60)

    pg.quit()

run_game()
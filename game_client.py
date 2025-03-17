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
    for layer in tmx_data.layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    screen.blit(tile, (x * tmx_data.tilewidth + world_offset[0], 
                                       y * tmx_data.tileheight + world_offset[1]))



def run_game():
    pg.init()

    screen = pg.display.set_mode((1000, 650))
    clock = pg.time.Clock()
    my_player = {'x': 400, 'y': 400, 'width': 20, 'height': 20, 'id': 0}
    players = [
        {"x": 300, "y": 200, "width": 20, "height": 20, "id": 1},
        {"x": 400, "y": 300, "width": 20, "height": 20, "id": 2},
        {"x": 700, "y": 500, "width": 20, "height": 20, "id": 3}
    ]
    used_weapon=0
    weapons= [
        {"damage":25, "range": 50,'bulet_speed':0.2,'amo':50,'weapon_id':1},
        {"damage":20,"range": 100,'bulet_speed':0.3,'amo':20,'weapon_id':2},
        {"damage":15, "range": 200,'bulet_speed':0.5,'amo':7,'weapon_id':3}
        
        
    ]
    BLACK = (0, 0, 0)
    move_offset = (0, 0)
    world_offset = (0, 0)
    #tmx_data = load_tmx_map("c:/networks/webroot/map.tmx")
    acceleration = 0.1
    moving = False
    colision_player=0
    direction = 0 #like m in y=mx+b
    setup=0#like b in y=mx+b

    x = 400
    y = 400
    
    #my_sprite = Pmodel1.Player.convert_to_sprite(my_player['x'], my_player['y'], my_player['height'], my_player['width'],my_player['id'])
    #players_sprites = [
     #   Pmodel1.Player.convert_to_sprite(player['x'], player['y'], player['height'], player['width'], player['id'])
      #  for player in players
    #]
    my_sprite={
        "image": pg.Surface((my_player["width"], my_player["height"])),
        "rect": pg.Rect(500,325, my_player["width"], my_player["height"]),
    }
    
    players_sprites = [
    {
        "image": pg.Surface((player["width"], player["height"])),
        "rect": pg.Rect(player["x"], player["y"], player["width"], player["height"]),
    }
    for player in players
    ]
    obj = Pmodel1.Player(
        x,
        y,
        my_player['height'],
        my_player['width'],
        my_player['id'],
        10,
        1,
        1,
        100,
        100,
        0.1,
        players,
        False,
        (0, 0),
        0,
        screen,
        players_sprites,
        my_sprite
    )  # Create PlayerSprite objects for each player
   # players_sprites = [Pmodel1.PlayerSprite(player['x'], player['y'], player['width'], player['height']) for player in players]
    #my_player_sprite = Pmodel1.PlayerSprite(my_player['x'], my_player['y'], my_player['width'], my_player['height'])
    Socket = ClientSocket.ClientServer()
    Socket.connect()
    players = Socket.run_conn(obj.convert_to_json())
    #print (players)
    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                target_pos = pg.mouse.get_pos()
                move_offset = (target_pos[0] - 500, target_pos[1] - 325)
                moving = True
            elif event.type == pg.MOUSEBUTTONUP and event.button == 3:
                weapons[used_weapon]['amo']-=1
                target_pos2 = pg.mouse.get_pos()
                shot_offset = (target_pos2[0] - 500, target_pos2[1] - 325)
                direction = (0- (325 - target_pos2[1])) / (0- (target_pos2[0] - 500))
                shot_offset[0]=(shot_offset/abs(shot_offset))*math.sqrt(weapons[used_weapon]['range']/2-direction*direction/2)
                shot_offset[1]=direction*shot_offset[0]
                 

                obj.shoot(used_weapon)
        collisions = []
        for player in players_sprites:
            if my_sprite['rect'].colliderect(player['rect']):  # Check collision using rect
                target_pos = (500,325)
                # Apply knockback based on movement direction
                if move_offset[0] > 0:  # Moving right
                    tp=475  # Knockback to the left)
                elif move_offset[0] < 0:  # Moving left
                    tp=525  # Knockback to the right
                if move_offset[1] > 0:  # Moving down
                    tp2= 300  # Knockback upward
                elif move_offset[1] < 0:  # Moving up
                    tp2=350  # Knockback downward
                move_offset = (tp - 500, tp2 - 325)
                # Stop movement in the direction of the collision

        # Update player position
        
        
        players = Socket.run_conn(obj.convert_to_json())

        for i in range (0,3):
            #players [i]['x']=players [i]['x']+1
            #players [i]['y']=players [i]['y']+1
            players_sprites[i]['rect'].x=players[i]['x']
            players_sprites[i]['rect'].y=players[i]['y']
        #print(players)
        #print (my_player)
        #if colision_id[0] == 0:
        moving, move_offset, x, y = obj.move(players_sprites, acceleration, move_offset, moving) 

        obj.set_x_y(x, y)
        screen.fill(BLACK)
        world_offset = (500 - x, 325 - y)
        #draw_map(screen, tmx_data, world_offset)
        obj.print_players(players_sprites,screen)
        pg.display.flip()
        clock.tick(60)

    pg.quit()

run_game()
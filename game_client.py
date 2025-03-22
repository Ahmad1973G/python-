import pygame as pg
import json
import Pmodel1
import ClientSocket
import threading
import time
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

def big_boom_boom(players,screen,red,range):
    pg.draw.circle(screen,red,(500,325),range, width=0)
    pg.display.flip()
    time.sleep(0.5)
    for player in players:
        if math.sqrt((player['x']-500)**2+(325-player['y'])**2)<=range+10:
            print('player', str(player['id']) ,'got hit by big boom boom')

def shoot(weapons,players_sprites,bullet_sprite,screen):
    while True:
        if shared_data['fire']:
            if weapons[shared_data['used_weapon']]['ammo']==0:
                print ('out of ammo')
            else:
                hit=False
                range1=1
                weapons[shared_data['used_weapon']]['ammo'] -= 1
                shot_offset = list(pg.mouse.get_pos())
                shot_offset[0] -= 500
                shot_offset[1] = 325 - shot_offset[1]
                added_dis=range1*weapons[shared_data['used_weapon']]['bulet_speed']
                while abs(range1) < weapons[shared_data['used_weapon']]['range']-1 and not hit:
                    range1+=added_dis
                    # direction = (0- (325 - shot_offset[1])) / (0- (shot_offset[0] - 500))
                    try:
                        direction = (0 - shot_offset[1]) / (0 - shot_offset[0])
                        shot_offset[0] = (shot_offset[0] / abs(shot_offset[0])) * math.sqrt(
                            range1 / (direction * direction + 1))
                        shot_offset[1] = direction * shot_offset[0]  # shot offset is the x,y of the max distance of shot
                    except ZeroDivisionError:
                        shot_offset[1]=(shot_offset[1] / abs(shot_offset[1])*math.sqrt(range1))
                        shot_offset[0]=0
                    bullet_sprite['rect'].x=shot_offset[0]+500
                    bullet_sprite['rect'].y=325-shot_offset[1]
                    bullet_sprite['image'].fill((0, 255, 0))
                    screen.blit(bullet_sprite['image'], bullet_sprite['rect'])
                    pg.display.flip()
                    #--------------------------------------------------------------
                    for i in range (0,players_sprites.__len__()):
                        if players_sprites[i]['rect'].colliderect(bullet_sprite['rect']):
                            print("hit" + " "+str(i)+' '+'with weapon'+ ' '+str(shared_data['used_weapon']+1))
                            hit =True
                            shared_data['fire']=False

def draw_map(screen, tmx_data, world_offset):
    """Draw the TMX map with an offset to simulate camera movement."""
    for layer in tmx_data.layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    screen.blit(tile, (x * tmx_data.tilewidth + world_offset[0],
                                        y * tmx_data.tileheight + world_offset[1]))

shared_data = {"fire": False, "used_weapon": 0}
lock = threading.Lock()

def run_game():
    pg.init()
    screen = pg.display.set_mode((1000, 650))
    clock = pg.time.Clock()

    my_player = {'x': 400, 'y': 500, 'width': 20, 'height': 20, 'id': 0,'hp':100}
    players = [
        {"x": 300, "y": 200, "width": 20, "height": 20, "id": 1},
        {"x": 300, "y": 400, "width": 20, "height": 20, "id": 2},
        {"x": 700, "y": 500, "width": 20, "height": 20, "id": 3}
    ]

    used_weapon = 2
    weapons = [
        {"damage": 25, "range": 10000, 'bulet_speed': 70, 'ammo': 50, 'weapon_id': 1},
        {"damage": 20, "range": 70000, 'bulet_speed': 80, 'ammo': 20, 'weapon_id': 2},
        {"damage": 15, "range": 120000, 'bulet_speed': 100, 'ammo': 7, 'weapon_id': 3}
    ]

    granade_range=200
    BLACK = (0, 0, 0)
    move_offset = (0, 0)
    world_offset = (0, 0)
    # tmx_data = load_tmx_map("c:/networks/webroot/map.tmx")
    acceleration = 0.05
    moving = False
    colision_player = 0
    direction = 0  # like m in y=mx+b
    RED = (255, 0, 0)
    sum_offset = [0, 0]

    bullet_sprite={
        "image": pg.Surface((10,10)),
        "rect": pg.Rect(500, 325, 10,10),
    }

    my_sprite = {
        "image": pg.Surface((my_player["width"], my_player["height"])),
        "rect": pg.Rect(500, 325, my_player["width"], my_player["height"]),
    }

    players_sprites = [
        {
            "image": pg.Surface((player["width"], player["height"])),
            "rect": pg.Rect(player["x"], player["y"], player["width"], player["height"]),
        }
        for player in players
    ]

    obj = Pmodel1.Player(
        my_player,
        10,
        1,
        1,
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

    # Initialize Items
    health_kit = Pmodel1.HealthKit()
    ammo_pack = Pmodel1.AmmoPack()

    running = True
    fire = False
    h = None
    g = None
    thread_shooting = threading.Thread(target=shoot, args=(weapons,players_sprites, bullet_sprite, screen))
    thread_shooting.daemon = True
    thread_shooting.start()

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                target_pos = pg.mouse.get_pos()
                move_offset = (target_pos[0] - 500, target_pos[1] - 325)
                moving = True
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                shared_data['fire'] = True
            elif event.type == pg.KEYDOWN:  # Check if a key was pressed
                if event.key == pg.K_1:
                    shared_data['used_weapon'] = 0
                elif event.key == pg.K_2:
                    shared_data['used_weapon'] = 1
                elif event.key == pg.K_3:
                    shared_data['used_weapon'] = 2
                elif event.key == pg.K_q:
                    obj.power.UsePower1(obj, 5000)  # Speed boost for 5 seconds
                    print("Speed boost activated")
                elif event.key == pg.K_w:
                    obj.power.UsePower2(obj, 5000)  # Shield for 5 seconds
                    print("Shield activated")
                elif event.key == pg.K_e:
                    obj.power.UsePower3(obj)  # Replenish
                    print("Replenish activated")
                elif event.key == pg.K_4:  # Use Health Kit
                    health_kit.use(obj)
                    print("Health Kit used")
                elif event.key == pg.K_5:  # Use Ammo Pack
                    ammo_pack.use(obj)
                    print("Ammo Pack used")

        # Stop movement in the direction of the collision
        # Update player position
        players = [
            {"x": 300, "y": 200, "width": 20, "height": 20, "id": 1},
            {"x": 300, "y": 400, "width": 20, "height": 20, "id": 2},
            {"x": 700, "y": 500, "width": 20, "height": 20, "id": 3}
        ]

        for player in players:
            player['x'] = player['x'] - obj.my_player['x'] + 500
            player['y'] = player['y'] - obj.my_player['y'] + 325

        players_sprites = [
            {
                "image": pg.Surface((player["width"], player["height"])),
                "rect": pg.Rect(player["x"], player["y"], player["width"], player["height"]),
            }
            for player in players
        ]

        sum_offset[0] -= move_offset[0] * acceleration
        sum_offset[1] -= move_offset[1] * acceleration
        obj.update_players_sprites(players, players_sprites)
        # Call the update method in the Player class
        obj.update()
        moving, move_offset, x, y = obj.move(players_sprites, acceleration, move_offset, moving)
        time.sleep(0.0001)

        for i in range(0, players.__len__() - 1):
            players[i]['x'] = players_sprites[i]['rect'].x
            players[i]['y'] = players_sprites[i]['rect'].y
        obj.update_players_sprites(players, players_sprites)

        screen.fill(BLACK)
        world_offset = (500 - my_player['x'], 325 - my_player['y'])
        # draw_map(screen, tmx_data, world_offset)
        obj.print_players(players_sprites, screen)
        pg.display.flip()
        clock.tick(60)

    pg.quit()

run_game()

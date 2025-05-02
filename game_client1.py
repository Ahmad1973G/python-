import pygame as pg
import json

from pygame.examples.music_drop_fade import starting_pos
import random
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


def bomb(players_sprites, screen, red, Brange, my_player, Socket):
    while True:
        if shared_data['bomb']:
            with lock:    
                print("CLIENT; player activated bomb")
                bomb_x = my_player['x']
                bomb_y = my_player['y']
                bomb_range = Brange
                explosion_center = (bomb_x - my_player['x'] + 500, bomb_y - my_player['y'] + 325)

                pg.draw.circle(screen, red, explosion_center, bomb_range, width=0)
                pg.display.flip()

                for player_id, player_data in players_sprites.items():
                    player_center = player_data['rect'].center
                    distance = math.sqrt(
                        (player_center[0] - explosion_center[0]) ** 2 +
                        (player_center[1] - explosion_center[1]) ** 2
                    )
                    if distance <= bomb_range:
                        print(f"Player {player_id} hit by explosion!")
                
                my_player_center = (500, 325)
                self_distance = math.sqrt(
                    (my_player_center[0] - explosion_center[0]) ** 2 +
                    (my_player_center[1] - explosion_center[1]) ** 2
                )
                if self_distance <= bomb_range:
                    print("CLIENT; You were hit by the explosion!")
                    
                Socket.sendBOOM(bomb_x, bomb_y, bomb_range)
                shared_data['bomb'] = False

        with lock:
            for key, data in list(shared_data['recived'].items()):
                if 'explode' in data:
                    print("CLIENT; someone activated bomb")
                    bomb_x = int(float(data['explode'][0]))
                    bomb_y = int(float(data['explode'][1]))
                    bomb_range = int(float(data['explode'][2]))
                    explosion_center = (bomb_x - my_player['x'] + 500, bomb_y - my_player['y'] + 325)
                    
                    pg.draw.circle(screen, red, explosion_center, bomb_range, width=0)
                    pg.display.flip()
                    time.sleep(0.5)
                    
                    my_player_center = (500, 325)
                    self_distance = math.sqrt(
                        (my_player_center[0] - explosion_center[0]) ** 2 +
                        (my_player_center[1] - explosion_center[1]) ** 2
                    )
                    if self_distance <= bomb_range:
                        print("CLIENT; You were hit by the explosion!")
                    
                    del shared_data['recived'][key]

        time.sleep(0.02)  # Add a small delay to reduce CPU usage

        
                


# def sendmovement(x,y):
# while True:
# if moving:
# Socket.sendMOVE(x,y)
def shoot(weapons, players_sprites, bullet_sprite, screen, my_player, Socket):
    hit = False
    # pg.mixer.init()
    # sound_effect = pg.mixer.Sound("C:/Users/User/Desktop/Documents/shot.wav")
    # sound_effect.set_volume(0.5)
    while True:
        shot_offset = (0, 0)
        if shared_data['fire']:

            if weapons[shared_data['used_weapon']]['ammo'] == 0:
                print('out of ammo')
            else:
                # sound_effect.play()
                hit = False
                range1 = 1
                weapons[shared_data['used_weapon']]['ammo'] -= 1
                shot_offset = list(pg.mouse.get_pos())
                shot_offset[0] -= 500
                shot_offset[1] = 325 - shot_offset[1]
                added_dis = range1 * weapons[shared_data['used_weapon']]['bulet_speed']

                while abs(range1) < weapons[shared_data['used_weapon']]['range'] - 1 and not hit:
                    range1 += added_dis
                    # direction = (0- (325 - shot_offset[1])) / (0- (shot_offset[0] - 500))
                    try:
                        direction = (0 - shot_offset[1]) / (0 - shot_offset[0])
                        shot_offset[0] = (shot_offset[0] / abs(shot_offset[0])) * math.sqrt(
                            range1 / (direction * direction + 1))
                        shot_offset[1] = direction * shot_offset[
                            0]  # shot offset is the x,y of the max distance of shot
                    except ZeroDivisionError:
                        shot_offset[1] = (shot_offset[1] / abs(shot_offset[1]) * math.sqrt(range1))
                        shot_offset[0] = 0
                    bullet_sprite['rect'].x = shot_offset[0] + 500
                    bullet_sprite['rect'].y = 325 - shot_offset[1]
                    bullet_sprite['image'].fill((0, 255, 0))
                    with lock:
                        screen.blit(bullet_sprite['image'], bullet_sprite['rect'])
                        pg.display.flip()

                    # --------------------------------------------------------------
                    for key, data in players_sprites.items():
                        if data['rect'].colliderect(bullet_sprite['rect']):
                            print(
                                "hit" + " " + key + ' ' + 'with weapon' + ' ' + str(shared_data['used_weapon'] + 1))
                            hit = True
                end1 = (shot_offset[0] / abs(shot_offset[0])) * math.sqrt(
                    weapons[shared_data['used_weapon']]['range'] / (direction * direction + 1))
                end2 = direction * end1
                end1 += 500
                end2 = 325 - end2
                end1 += my_player['x'] - 500
                end2 += my_player['y'] - 325
                Socket.sendSHOOT(my_player['x'], my_player['y'], end1, end2, shared_data['used_weapon'])
                shared_data['fire'] = False
        with lock_shared_data:
            temp = shared_data['recived']
        if temp != {}:
            for key, data in temp.items():
                if 'shoot' in data:
                    start_pos = [int(float(data['shoot'][0])), int(float(data['shoot'][1]))]
                    end_pos = [int(float(data['shoot'][2])), int(float(data['shoot'][3]))]
                    start_pos[0] -= my_player['x'] - 500
                    start_pos[1] -= my_player['y'] - 325
                    end_pos[0] -= my_player['x'] - 500
                    end_pos[1] -= my_player['y'] - 325
                    Red = (255, 0, 0)

                    # --------------------------------------------------------------------------------
                    hit2 = False
                    range1 = 1
                    end_pos[0] -= start_pos[0]  # setting players position as rashit hatsirim
                    end_pos[1] = start_pos[1] - end_pos[1]
                    added_dis = range1 * weapons[int(data['shoot'][4])]['bulet_speed']

                    while abs(range1) < weapons[int(data['shoot'][4])]['range'] - 1 and not hit2:
                        range1 += added_dis
                        try:
                            direction = (0 - end_pos[1]) / (0 - end_pos[0])
                            end_pos[0] = (end_pos[0] / abs(end_pos[0])) * math.sqrt(
                                range1 / (direction * direction + 1))
                            end_pos[1] = direction * end_pos[0]
                        except ZeroDivisionError:
                            end_pos[1] = (end_pos[1] / abs(end_pos[1]) * math.sqrt(range1))
                            end_pos[0] = 0
                        bullet_sprite['image'].fill((255, 0, 255))
                        bullet_sprite['rect'] = bullet_sprite['image'].get_rect(
                            center=(end_pos[0] + start_pos[0], start_pos[1] - end_pos[1]))
                        with lock:
                            screen.blit(bullet_sprite['image'], bullet_sprite['rect'])
                            pg.display.flip()
                        image = pg.Surface((60, 60))
                        image.fill(pg.Color('blue'))
                        rect = image.get_rect(center=(500, 325))
                        # --------------------------------------------------------------
                        if rect.colliderect(bullet_sprite['rect']):
                            print("got hit")
                            #    Socket.sendDAMAGE(weapons[int(data['shoot'][4])]['damage'])
                            my_player['hp'] -= weapons[int(data['shoot'][4])]['damage']
                            hit2 = True

def apply_item_effect(item, my_player, weapons, shared_data, obj):
    """Apply the effect of the item to the player."""
    if item['type'] == 'health':
        my_player['hp'] = min(my_player['hp'] + 25, 100)  # Heal the player
        print(f"Health increased to {my_player['hp']}")
    elif item['type'] == 'ammo':
        weapons[shared_data['used_weapon']]['ammo'] = min(
            weapons[shared_data['used_weapon']]['ammo'] + 5,
            weapons[shared_data['used_weapon']]['max_ammo']
        )
        print(f"Ammo for weapon {shared_data['used_weapon']} increased to {weapons[shared_data['used_weapon']]['ammo']}")
    elif item['type'] == 'cooldown_refresh':
        obj.speed_cooldown_end_time = 0  # Reset speed powerup cooldown
        obj.invulnerability_cooldown_end_time = 0  # Reset invulnerability cooldown
        print("Powerup cooldowns refreshed!")


def check_if_dead(hp):
    print("dead")
    x = 500
    y = 500
    dis_to_mid = [x - 500, y - 325]
    return x, y, dis_to_mid, 50, 20, 7


shared_data = {"fire": False, "bomb": False, "used_weapon": 0, 'got_shot': False, 'recived': {}}

lock_shared_data = threading.Lock()
lock = threading.Lock()


def get_collidable_tiles(tmx_data, collidable_tileset_name="Obstacles"):
    """Returns a set of tile coordinates that are collidable."""
    collidable_tiles = set()
    for layer in tmx_data.layers:
        if isinstance(layer, pytmx.TiledObjectGroup):
            if layer.name == "no walk no shoot":
                for obj in layer:
                    # Add the coordinates of the collidable tile to the set
                    new_tile_tup = obj.x - 500, obj.width, obj.y - 330, obj.height
                    # collidable_tiles.add((obj.x // tmx_data.tilewidth, obj.y // tmx_data.tileheight))
                    collidable_tiles.add(new_tile_tup)
    return collidable_tiles


def check_collision(player_rect, coll_obj_x, coll_obj_w, coll_obj_y, coll_obj_h):
    if player_rect.x > coll_obj_x + coll_obj_w or player_rect.y < coll_obj_y - coll_obj_h:
        return False
    if player_rect.x + player_rect.width < coll_obj_x or player_rect.y - player_rect.height > coll_obj_y:
        return False
    return True


def check_tile_collision(player_rect, collidable_tiles, tilewidth, tileheight):
    """Checks if the player collides with any of the collidable tiles."""
    for coll_obj_x, coll_obj_w, coll_obj_y, coll_obj_h in collidable_tiles:
        if check_collision(player_rect, coll_obj_x, coll_obj_w, coll_obj_y, coll_obj_h):
            print(coll_obj_x, coll_obj_w, coll_obj_y, coll_obj_h)
            return True
    print("No collision")
    return False

def check_item_collision(my_player, items, weapons, shared_data, obj):
    """Check if the player collides with any items and apply their effects."""
    player_rect = pg.Rect(my_player['x'], my_player['y'], my_player['width'], my_player['height'])
    for item in items[:]:  # Iterate over a copy of the items list
        item_rect = pg.Rect(item['x'], item['y'], item['width'], item['height'])
        if player_rect.colliderect(item_rect):
            apply_item_effect(item, my_player, weapons, shared_data, obj)
            items.remove(item)  # Remove the item after it is picked up
            print(f"Picked up item: {item['type']}")


def run_game():
    pg.init()
    with lock:
        screen = pg.display.set_mode((1000, 650))
    clock = pg.time.Clock()
    my_player = {'x': 300, 'y': 300, 'width': 60, 'height': 60, 'id': 0,
                 'hp': 100}
    dis_to_mid = [my_player['x'] - 500, my_player['y'] - 325]
    players = {}

    weapons = [
        {"damage": 25, "range": 10000, 'bulet_speed': 70, 'ammo': 50, 'max_ammo': 50, 'weapon_id': 1},
        {"damage": 20, "range": 70000, 'bulet_speed': 80, 'ammo': 20, 'max_ammo': 20, 'weapon_id': 2},
        {"damage": 15, "range": 120000, 'bulet_speed': 100, 'ammo': 7, 'max_ammo': 7, 'weapon_id': 3}

    ]

    items = [
    {'x': 200, 'y': 200, 'width': 20, 'height': 20, 'type': 'health'},
    {'x': 400, 'y': 300, 'width': 20, 'height': 20, 'type': 'ammo'},
    {'x': 600, 'y': 400, 'width': 20, 'height': 20, 'type': 'cooldown_refresh'},
]
    
    moving = False
    move_x = 0
    move_y = 0
    angle = 0
    knockback = 0
    death = pg.image.load('dead.png').convert()
    granade_range = 200
    BLACK = (0, 0, 0)
    move_offset = (0, 0)
    world_offset = (0, 0)
    tmx_data = pytmx.load_pygame("c:/webroot/map.tmx")  # <<< your TMX file here
    collidable_tiles = get_collidable_tiles(tmx_data,
                                            collidable_tileset_name="Obstacles")  # Get collidable tile coordinates
    tile_width = tmx_data.tilewidth
    tile_height = tmx_data.tileheight
    map_width = tmx_data.width
    map_height = tmx_data.height
    SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 650
    acceleration = 0.1
    direction = 0  # like m in y=mx+b
    RED = (255, 0, 0)
    sum_offset = [0, 0]
    # my_sprite = Pmodel1.Player.convert_to_sprite(my_player['x'], my_player['y'], my_player['height'], my_player['width'],my_player['id'])
    # players_sprites = [
    #   Pmodel1.Player.convert_to_sprite(player['x'], player['y'], player['height'], player['width'], player['id'])
    #  for player in players
    # ]
    bullet_sprite = {
        "image": pg.Surface((10, 10)),
        "rect": pg.Rect(500, 325, 10, 10),
    }
    my_sprite = {
        "image": pg.Surface((my_player["width"], my_player["height"])),
        "rect": pg.Rect(500, 325, my_player["width"], my_player["height"])
    }

    players_sprites = {}
    with lock:
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
            my_sprite,
            weapons
        )  # Create PlayerSprite objects for each player
    # players_sprites = [Pmodel1.PlayerSprite(player['x'], player['y'], player['width'], player['height']) for player in players]
    # my_player_sprite = Pmodel1.PlayerSprite(my_player['x'], my_player['y'], my_player['width'], my_player['height'])
    # --------------------------------------------------------------------------------
    Socket = ClientSocket.ClientServer()
    Socket.connect()
    recived = Socket.requestDATAFULL()
    if recived != {}:
        for key, data in recived.items():
            old_player = {
                'x': int(float(data['x']) - float(dis_to_mid[1])),
                'y': int(float(data['y']) - float(dis_to_mid[1])),
                'width': 60,
                'height': 60,
                'hp': 100,
                'angle': 0
            }
            players[key] = old_player
            old_player = {
                'image': pg.Surface((players[key]['width'], players[key]['height'])),
                'rect': pg.Rect(players[key]['x'], players[key]['y'], players[key]['width'], players[key]['height'])
            }
            players_sprites[key] = old_player
    else:
        players = {}
        players_sprites = {}

    Socket.sendMOVE(my_player['x'], my_player['y'])

    # print (players)
    running = True
    h = None
    g = None
    # thread_movement = threading.Thread(target=sendmovement, args=())
    thread_shooting = threading.Thread(target=shoot,
                                       args=(weapons, players_sprites, bullet_sprite, screen, my_player, Socket))
    thread_shooting.daemon = True
    thread_shooting.start()

    thread_bomb = threading.Thread(target=bomb, args=(players_sprites, screen, RED, granade_range, my_player, Socket))
    thread_bomb.daemon = True
    thread_bomb.start()
    # thread_movement.start()
    while running:

        
        #Checks for Powerups and items that don't require server connection
        obj.check_speed()
        obj.check_invulnerability()
        #check_item_collision()
        #Checks for Powerups and items that don't require server connection

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                shared_data['fire'] = True
            elif event.type == pg.MOUSEMOTION:
                mouse = pg.mouse.get_pos()
                if mouse[0] == 500:
                    if mouse[1] == 325:
                        angle = 0
                    else:
                        angle = (1 + (-(325 - mouse[1])) / abs(325 - mouse[1])) * 90
                else:
                    direction = (0 - (325 - mouse[1])) / (0 - (mouse[0] - 500))
                    angle = math.atan(direction)
                    angle = math.degrees(angle)
                    if direction == 0:
                        angle = 180 + (mouse[0] / abs(mouse[0])) * 90
                    else:
                        angle = (direction / abs(direction)) * (
                                (-(mouse[0] - 500)) / abs(mouse[0] - 500)) * 90 + angle + (
                                        1 + (-direction) / abs(direction)) * 90
                Socket.sendANGLE(angle)
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_1:
                    shared_data['used_weapon'] = 0
                elif event.key == pg.K_2:
                    shared_data['used_weapon'] = 1
                elif event.key == pg.K_3:
                    shared_data['used_weapon'] = 2
                elif event.key == pg.K_q:
                    shared_data['bomb'] = True
                    time.sleep(0.5)
                elif event.key == pg.K_r:
                    weapons[shared_data['used_weapon']]['ammo'] = weapons[shared_data['used_weapon']]['max_ammo']
                elif event.key == pg.K_e:
                    if obj.speed_power == False:
                        obj.speed_up(5)
                        print("CLIENT; speed up")
                elif event.key == pg.K_t:
                    if obj.invulnerability == False:
                        obj.activate_invulnerability(5)
                        print("CLIENT; Invulnerability")

                
        keys = pg.key.get_pressed()
        # Check for collisions with nearby collision rects
        #print(f"Here pressed {keys}")
        #res = check_tile_collision(my_player, collidable_tiles, tile_width, tile_height)
        #print("Finished")

        

        #print(res)
        if knockback == 0:
            obj.check_speed()
            obj.check_invulnerability()
            if keys[pg.K_w]:
                new_rect = pg.Rect(my_player['x'], my_player['y'] - obj.speed, my_player['width'], my_player['height'])
                if not check_tile_collision(new_rect, collidable_tiles, tile_width, tile_height):
                    my_player['y'] -= obj.speed
                    move_y = obj.speed
            if keys[pg.K_s]:
                new_rect = pg.Rect(my_player['x'], my_player['y'] + obj.speed, my_player['width'], my_player['height'])
                if not check_tile_collision(new_rect, collidable_tiles, tile_width, tile_height):
                    my_player['y'] += obj.speed
                    move_y = -obj.speed
            if keys[pg.K_a]:
                new_rect = pg.Rect(my_player['x'] - obj.speed, my_player['y'], my_player['width'], my_player['height'])
                if not check_tile_collision(new_rect, collidable_tiles, tile_width, tile_height):
                    my_player['x'] -= obj.speed
                    move_x = obj.speed
            if keys[pg.K_d]:
                new_rect = pg.Rect(my_player['x'] + obj.speed, my_player['y'], my_player['width'], my_player['height'])
                if not check_tile_collision(new_rect, collidable_tiles, tile_width, tile_height):
                    my_player['x'] += obj.speed
                    move_x = -obj.speed
        else:
            knockback -= 1

        if my_player['hp'] <= 0:
            my_player['hp'] = 100
            my_player['x'] = 500
            my_player['y'] = 500
            for key, data in players.items():
                data['x'] += dis_to_mid[0] - (my_player['x'] - 500)
                data['y'] += dis_to_mid[1] - (my_player['y'] - 325)
            dis_to_mid = [my_player['x'] - 500, my_player['y'] - 325]
            weapons[0]['ammo'] = weapons[0]['max_ammo']
            weapons[1]['ammo'] = weapons[1]['max_ammo']
            weapons[2]['ammo'] = weapons[2]['max_ammo']
            sum_offset = [0, 0]
            with lock:
                screen.blit(death, (0, 0))
            pg.display.flip()
            # kys = pg.key.get_pressed()
            # while not kys[pg.K_r]:
            #    kys = pg.key.get_pressed()
            time.sleep(5)
            Socket.sendMOVE(my_player['x'], my_player['y'])
        recived = Socket.requestDATA()

        with lock_shared_data:
            shared_data['recived'] = recived

        found = False
        for key, data in recived.items():
            if key in players:
                if 'x' in data:
                    players[key]['x'] = int(float(data['x']) - float(dis_to_mid[0]))
                    players[key]['y'] = int(float(data['y']) - float(dis_to_mid[1]))

                if 'hp' in data:
                    players[key]['hp'] = data['hp']
                    if data['hp'] <= 0:
                        del (players[key])
                    # check_if_they_dead(players[key]['hp'])
                if 'angle' in data:
                    players[key]['angle'] = data['angle']
            elif 'x' in data and 'y' in data:
                new_player = {
                    'x': int(float(data['x']) - float(dis_to_mid[0])),
                    'y': int(float(data['y']) - float(dis_to_mid[1])),
                    'width': 60,
                    'height': 60,
                    'hp': 100,
                    'angle': 0
                }
                players[key] = new_player
                new_player = {
                    'image': pg.Surface((players[key]['width'], players[key]['height'])),
                    'rect': pg.Rect(players[key]['x'], players[key]['y'], players[key]['width'], players[key]['height'])
                }
                players_sprites[key] = new_player

        if players != {}:
            sum_offset[0] += move_x
            sum_offset[1] += move_y
            for key, data in players.items():
                players_sprites[key]["image"] = pg.Surface((players[key]['width'], players[key]['height']))
                players_sprites[key]["rect"] = pg.Rect(int(data["x"] + sum_offset[0]), int(data["y"] + sum_offset[1]),
                                                       players[key]['width'], players[key]['height'])

        for key, data in players_sprites.items():
            if data['rect'].x >= (500 - my_player['width']) and data['rect'].x <= (500 + my_player['width']) and data[
                'rect'].y >= (325 - my_player['height']) and data['rect'].y <= (325 + my_player['height']):
                move_x = -move_x
                move_y = -move_y
                knockback = 8

        if move_x != 0 or move_y != 0:

            if knockback == 0:
                move_x = 0
                move_y = 0
            else:
                my_player['x'] -= move_x
                my_player['y'] -= move_y
            Socket.sendMOVE(my_player['x'], my_player['y'])
        world_offset = (500 - my_player['x'], 325 - my_player['y'])

        with lock:
            start_col = my_player['x'] // tile_width
            start_row = my_player['y'] // tile_height
            end_col = (my_player['x'] + SCREEN_WIDTH) // tile_width + 2
            end_row = (my_player['y'] + SCREEN_HEIGHT) // tile_height + 2

            # Draw visible tiles
            for layer in tmx_data.visible_layers:
                if isinstance(layer, pytmx.TiledTileLayer):
                    layer_index = tmx_data.layers.index(layer)  # <<< fix here
                    for x in range(start_col, end_col):
                        for y in range(start_row, end_row):
                            if 0 <= x < map_width and 0 <= y < map_height:
                                image = tmx_data.get_tile_image(x, y, layer_index)
                                if image:
                                    screen.blit(
                                        image,
                                        (x * tile_width - my_player['x'], y * tile_height - my_player['y'])
                                    )
        with lock:
            for item in items:
                item_rect = pg.Rect(item['x'] - my_player['x'] + 500, item['y'] - my_player['y'] + 325, item['width'], item['height'])
                if item['type'] == 'health':
                    color = (0, 255, 0)  # Green for health
                elif item['type'] == 'ammo':
                    color = (0, 0, 255)  # Blue for ammo
                elif item['type'] == 'cooldown_refresh':
                    color = (255, 255, 0)  # Yellow for cooldown refresh
                pg.draw.rect(screen, color, item_rect)
        
        check_item_collision(my_player, items, weapons, shared_data, obj)

        obj.print_players(players_sprites, players, angle)
        pg.display.flip()
        clock.tick(60)
    pg.quit()


run_game()

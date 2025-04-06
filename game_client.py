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


def big_boom_boom(players, screen, red, range):
    pg.draw.circle(screen, red, (500, 325), range, width=0)
    pg.display.flip()
    time.sleep(0.5)


# def sendmovement(x,y):
# while True:
# if moving:
# Socket.sendMOVE(x,y)
def shoot(weapons, players_sprites, bullet_sprite, screen, my_player):
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
                    screen.blit(bullet_sprite['image'], bullet_sprite['rect'])
                    pg.display.flip()

                    # --------------------------------------------------------------
                    for i in range(0, players_sprites.__len__()):
                        if players_sprites[i]['rect'].colliderect(bullet_sprite['rect']):
                            print(
                                "hit" + " " + str(i) + ' ' + 'with weapon' + ' ' + str(shared_data['used_weapon'] + 1))
                            hit = True
                end1 = (shot_offset[0] / abs(shot_offset[0])) * math.sqrt(
                    weapons[shared_data['used_weapon']]['range'] / (direction * direction + 1))
                end2 = direction * end1
                end1 += 500
                end2 = 325 - end2
                end1 += my_player['x'] - 500
                end2 += my_player['y'] - 325
                ClientSocket.ClientServer.sendSHOOT(int(my_player['x']), int(my_player['y']), int(end1), int(end2))
                shared_data['fire'] = False
        for key, data in shared_data['recived'].items():
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
                    screen.blit(bullet_sprite['image'], bullet_sprite['rect'])
                    pg.display.flip()
                    image = pg.Surface((20, 20))
                    image.fill(pg.Color('blue'))
                    rect = image.get_rect(center=(500, 325))
                    # --------------------------------------------------------------
                    if rect.colliderect(bullet_sprite['rect']):
                        print("got hit")
                        # my_player['hp']-=weapons[int(data['shoot'][4])]['damage']
                        my_player['hp'] -= weapons[0]['damage']
                        hit2 = True


def check_if_dead(hp):
    if hp == 0:
        print("dead")
        pg.quit()
        sys.exit()

def knockback(x, y, move_offset, moving, knockback_x, knockback_y):
    move_offset = (500 - x, y - 325)
    target_pos = (500, 325)
    moving = True
    tp = 500
    tp2 = 325
    # Apply knockback based on movement direction
    if move_offset[0] > 0:  # Moving right
        tp -= knockback_x  # Knockback to the left)
    elif move_offset[0] < 0:  # left
        tp += knockback_x  # Knockback to the right
    if move_offset[1] > 0:  # Moving down
        tp2 -= knockback_y  # Knockback upward
    elif move_offset[1] < 0:  # Moving up
        tp2 += knockback_y  # Knockback downward
    move_offset = (tp - 500, tp2 - 325)
    return move_offset, moving, target_pos


def get_collision_rects(tmx_data):
    collision_rects = []
    tile_width = tmx_data.tilewidth
    tile_height = tmx_data.tileheight

    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            if layer.properties.get('collidable'):  # This is what matters!
                for x, y, gid in layer:
                    if gid != 0:
                        rect = pg.Rect(x * tile_width, y * tile_height, tile_width, tile_height)
                        collision_rects.append(rect)
    return collision_rects


def draw_map(screen, map_surface, world_offset):
    """Draw the TMX map onto the screen."""
    screen.blit(map_surface, world_offset)


def render_map(tmx_data):
    """Render the TMX map onto a surface once."""
    map_surface = pg.Surface((tmx_data.width * tmx_data.tilewidth,
                              tmx_data.height * tmx_data.tileheight))

    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    map_surface.blit(tile, (x * tmx_data.tilewidth, y * tmx_data.tileheight))

    return map_surface


shared_data = {"fire": False, "used_weapon": 0, 'move_offset': (500, 325), 'got_shot': False, 'recived': {}}
server_connection = ClientSocket.ClientServer
lock = threading.Lock()


def get_no_walk_no_shoot_collision_rects(tmx_data):
    collision_rects = []
    for layer in tmx_data.layers:
        if layer.name.lower() == "no walk no shoot":
            if isinstance(layer, pytmx.TiledObjectGroup):
                for obj in layer:
                    rect = pg.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                    collision_rects.append(rect)
            elif isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid != 0:
                        rect = pg.Rect(x * tmx_data.tilewidth, y * tmx_data.tileheight,
                                       tmx_data.tilewidth, tmx_data.tileheight)
                        collision_rects.append(rect)
    return collision_rects


def run_game():
    pg.init()

    screen = pg.display.set_mode((1000, 650))
    clock = pg.time.Clock()
    my_player = {'x': 400, 'y': 400, 'width': 20, 'height': 20, 'id': 0,
                 'hp': 100}
    players = {}

    weapons = [
        {"damage": 25, "range": 10000, 'bulet_speed': 70, 'ammo': 50, 'max_ammo': 50, 'weapon_id': 1},
        {"damage": 20, "range": 70000, 'bulet_speed': 80, 'ammo': 20, 'max_ammo': 20, 'weapon_id': 2},
        {"damage": 15, "range": 120000, 'bulet_speed': 100, 'ammo': 7, 'max_ammo': 7, 'weapon_id': 3}

    ]
    moving = False
    granade_range = 200
    BLACK = (0, 0, 0)
    move_offset = (0, 0)
    world_offset = (0, 0)
    tmx_data = load_tmx_map("c:/webroot/map.tmx")
    no_walk_no_shoot_rects = get_no_walk_no_shoot_collision_rects(tmx_data)
    map_surface = render_map(tmx_data)
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
        "rect": pg.Rect(500, 325, my_player["width"], my_player["height"]),
    }

    players_sprites = {}

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
    shared_data['recived'] = Socket.requestDATAFULL()
    if shared_data['recived'] != {}:
        for key, data in shared_data['recived'].items():
            old_player = {
                'x': int(float(data['x']) - float(obj.my_player['x']) + 500),
                'y': int(float(data['y']) - float(obj.my_player['y']) + 325),
                'width': 20,
                'height': 20,
                'hp': 100
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
    thread_shooting = threading.Thread(target=shoot, args=(weapons, players_sprites, bullet_sprite, screen, my_player))
    thread_shooting.daemon = True
    thread_shooting.start()
    # thread_movement.start()
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
                # obj.shoot(used_weapon)
                elif event.key == pg.K_q:
                    big_boom_boom(players, screen, RED, granade_range)
                elif event.key == pg.K_r:
                    weapons[shared_data['used_weapon']]['ammo'] = weapons[shared_data['used_weapon']]['max_ammo']
                    # Stop movement in the direction of the collisio
        # Update player position
        # players = Socket.run_conn(obj.convert_to_json())
        # ---------------------------------------------------------------------------
        # updated_players = None#Socket.run_conn(obj.convert_to_json())
        # for player in updated_players:
        #    for key in player.keys():
        #        if player[key] is None:
        #            continue
        #        players[player['id']][key]=player[key]

        # if shared_data['move_offset'] != (500, 325):
        # move_offset = shared_data['move_offset']
        # shared_data['move_offset'] = (500, 325)
        check_if_dead(my_player['hp'])
        recived = Socket.requestDATA()
        shared_data['recived'] = recived
        if type(shared_data['recived']) is str:
            shared_data['recived'] = json.loads(recived)
        # shared_data['recived'] = {'268': {'x': 500, 'y': 325}, '2648': {'x': 50, 'y': 40}}
        found = False
        for key, data in shared_data['recived'].items():
            if key in players:
                if 'x' in data:
                    players[key]['x'] = int(float(data['x']) - float(obj.my_player['x']) + 500)+sum_offset[0]
                    players[key]['y'] = int(float(data['y']) - float(obj.my_player['y']) + 325)+sum_offset[1]

                if 'hp' in data:
                    players[key]['hp'] = data['hp']
                    # check_if_they_dead(players[key]['hp'])
            elif 'x' in data and 'y' in data:
                new_player = {
                    'x': int(float(data['x']) - float(obj.my_player['x']) + 500),
                    'y': int(float(data['y']) - float(obj.my_player['y']) + 325),
                    'width': 20,
                    'height': 20,
                    'hp': 100
                }
                players[key] = new_player
                new_player = {
                    'image': pg.Surface((players[key]['width'], players[key]['height'])),
                    'rect': pg.Rect(players[key]['x'], players[key]['y'], players[key]['width'], players[key]['height'])
                }
                players_sprites[key] = new_player

        if players != {}:
            for key, data in players.items():
                players_sprites[key]["image"] = pg.Surface((players[key]['width'],players[key]['height']))
                players_sprites[key]["rect"] = pg.Rect(int(data["x"]-(data['width']/2)), int(data["y"]-(data['height']/2)),players[key]['width'],players[key]['height'])
            sum_offset[0] -= move_offset[0] * acceleration
            sum_offset[1] -= move_offset[1] * acceleration
            # for i in range(0,players._len_()-1):
            # players [i]['x']+=1
            # players [i]['y']+=1
            # players_sprites[i]['rect'].x=players[i]['x']
            # players_sprites[i]['rect'].y=players[i]['y']
            # print(players)
            # print (my_player)
            # if colision_id[0] == 0:
            # Save original position
            # Save current position
            prev_x, prev_y = my_player['x'], my_player['y']

            # Attempt move
            moving, move_offset, my_player['x'], my_player['y'] = obj.move(moving, acceleration, move_offset, moving)

            # Update player's on-screen rect (centered)
            my_sprite['rect'].x = 500
            my_sprite['rect'].y = 325

            # Calculate camera offset
            offset_x = my_player['x'] - 500
            offset_y = my_player['y'] - 325

            # Check for collisions

            for tile_rect in no_walk_no_shoot_rects:
                tile_rect_screen = tile_rect.move(-offset_x, -offset_y)
                if my_sprite['rect'].colliderect(tile_rect_screen):
                    my_player['x'], my_player['y'] = prev_x, prev_y
                    break

            print(my_player['x'], my_player['y'])

            time.sleep(0.0001)
            screen.fill(BLACK)
            obj.print_players(players_sprites, screen)
        else:
            image = pg.Surface((20, 20))
            image.fill(pg.Color('blue'))
            rect = image.get_rect(center=(500, 325))
            screen.blit(image, rect)
        Socket.sendMOVE(my_player['x'], my_player['y'])

        world_offset = (500 - my_player['x'], 325 - my_player['y'])
        screen.blit(map_surface, world_offset)
        for key, data in players_sprites.items():
            if my_sprite['rect'].colliderect(data['rect']):  # Check collision using rect
                move_offset, moving, target_pos = knockback(data['rect'].x, data['rect'].y, move_offset, moving,
                                                            35, 35)

        # world_offset = (500 - my_player['x'], 325 - my_player['y'])
        # draw_map(screen, tmx_data, world_offset)
        moving, move_offset, my_player['x'], my_player['y'] = obj.move(acceleration, move_offset, moving)
        for key, data in players_sprites.items():
            players_sprites[key]['rect'].x += sum_offset[0]
            players_sprites[key]['rect'].y += sum_offset[1]
        if moving is True:
            Socket.sendMOVE(my_player['x'], my_player['y'])
        screen.fill(BLACK)
        obj.print_players(players_sprites, screen)
        pg.display.flip()
        clock.tick(60)
    pg.quit()


run_game()

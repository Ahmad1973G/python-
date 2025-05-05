import pygame as pg
import json
import tkinter as tk
from tkinter import messagebox, font
from tkinter import ttk
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
import startprotocol
from scipy.spatial import KDTree

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

                screen.fill((0, 0, 0))  # Clear screen
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

                    screen.fill((0, 0, 0))  # Clear screen
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


def check_if_dead(hp):
    print("dead")
    x = 500
    y = 500
    dis_to_mid = [x - 500, y - 325]
    return x, y, dis_to_mid, 50, 20, 7


shared_data = {"fire": False, "bomb": False, "used_weapon": 0, 'got_shot': False, 'recived': {}}

lock_shared_data = threading.Lock()
lock = threading.Lock()


def get_collidable_tiles(tmx_data):
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


def build_collision_kdtree(collidable_tiles):
    # Calculate center positions for KD-tree
    positions = [(x + w / 2, y - h / 2) for (x, w, y, h) in collidable_tiles]
    kd_tree = KDTree(positions)
    pos_to_tile = dict(zip(positions, collidable_tiles))
    return kd_tree, pos_to_tile


def check_collision_obj(player_rect, coll_obj_x, coll_obj_w, coll_obj_y, coll_obj_h):
    if player_rect.x - player_rect.width/2 > coll_obj_x + coll_obj_w or player_rect.y + player_rect.height/2 < coll_obj_y - coll_obj_h:
        return False
    if player_rect.x + player_rect.width/2 < coll_obj_x or player_rect.y - player_rect.height/2 > coll_obj_y:
        return False
    return True

def draw_health_bar(surface, x, y, current, max, bar_width=200, bar_height=25):
    ratio = current / max
    pg.draw.rect(surface, (255, 0, 0), (x, y, bar_width, bar_height))  # red background
    pg.draw.rect(surface, (0, 255, 0), (x, y, bar_width * ratio, bar_height))  # green foreground
    pg.draw.rect(surface, (0, 0, 0), (x, y, bar_width, bar_height), 2)  # border
     
    
def draw_chat_box(screen, font_chat, chat_log, chat_input, chat_input_active):
    box_width = 300
    box_x = 1000 - box_width  # Align to right side
    log_y = 350  # Starting Y position for log

    # Draw chat messages (right side)
    for msg in reversed(chat_log[-5:]):
        text_surface = font_chat.render(msg, True, (255, 0, 0))
        screen.blit(text_surface, (box_x + 10, log_y))
        log_y -= 25

    # Draw input box
    if chat_input_active:
        pg.draw.rect(screen, (0, 0, 0), (box_x, 575, box_width, 25))
        input_surface = font_chat.render(chat_input, True, (255, 0, 0))
        screen.blit(input_surface, (box_x + 5, 578))
        pg.draw.rect(screen, (255, 0, 0), (box_x, 575, box_width, 25), 1)


def chat_sync_loop(Socket, chat_log):
    while True:
        try:
            new_msgs = Socket.recvCHAT()
            if new_msgs is True:
                continue
            for cid, msg, seq in new_msgs:
                chat_log.append(f"{cid}: {msg}")
            time.sleep(0.5)
        except Exception as e:
            print("Chat loop error:", e)
            break
    
def draw_hotbar(screen, selected_slot, hotbar, screen_width=1000, screen_height=650, slot_size=50, inv_cols=9):
    hotbar_y = screen_height - slot_size - 20
    hotbar_x = (screen_width - inv_cols * slot_size) // 2

    for col in range(inv_cols):
        x = hotbar_x + col * slot_size
        y = hotbar_y

        # Background slot
        pg.draw.rect(screen, (60, 60, 60), (x, y, slot_size, slot_size))

        # Highlight selected slot
        if col == selected_slot:
            pg.draw.rect(screen, (255, 255, 0), (x - 2, y - 2, slot_size + 4, slot_size + 4), 3)

        # Border
        pg.draw.rect(screen, (255, 255, 255), (x, y, slot_size, slot_size), 2)

        # Draw item if exists
        item = hotbar[col]
        if item:
            screen.blit(item["image"], (x + 5, y + 5))

def load_item_image(filename, PICTURE_PATH, SLOT_SIZE):
    path = os.path.join(PICTURE_PATH, filename)
    image = pg.image.load(path).convert_alpha()
    return pg.transform.scale(image, (SLOT_SIZE - 10, SLOT_SIZE - 10))  # scale down


def check_item_collision(my_player, items, weapons, shared_data, obj, hotbar, selected_slot, SLOT_SIZE):
    """Check if the player collides with any items and apply their effects."""
    player_rect = pg.Rect(my_player['x'], my_player['y'], my_player['width'], my_player['height'])
    for item in items[:]:  # Iterate over a copy of the items list
        item_rect = pg.Rect(item['x'], item['y'], item['width'], item['height'])
        if player_rect.colliderect(item_rect):
            for slot in hotbar:
                if slot is None:
                    hotbar[selected_slot] = {"name": item['type'], "image" : load_item_image(item['type'] + ".png", "C:/python_game/python-", SLOT_SIZE)}
            items.remove(item)  # Remove the item after it is picked up
            print(f"Picked up item: {item['type']}")
            
            
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
        
        
def run_game():
    Socket = ClientSocket.ClientServer()
    Socket.connect()
    root = tk.Tk()
    app = startprotocol.ModernGameLogin(root, Socket)
    root.title("Login")
    root.mainloop()

    pg.init()
    with lock:
        screen = pg.display.set_mode((1000, 650))
        
    font_fps = pg.font.SysFont(None, 40)  # You can change font or size if you want
    font_chat = pg.font.SysFont(None, 24)  # You can change font or size if you want
    chat_input_active = False
    INV_ROWS = 3
    INV_COLS = 9
    SLOT_SIZE = 50
    picture_path = "C:/python_game/python-"  # raw string for Windows path
    weapon1_image = load_item_image("char_1.png", picture_path, SLOT_SIZE)
    weapon2_image = load_item_image("char_2.png", picture_path, SLOT_SIZE)
    weapon3_image = load_item_image("char_3.png", picture_path, SLOT_SIZE)
    hotbar = [{"name": "weapon1", "image": weapon1_image}, {"name": "weapon2", "image": weapon2_image}, 
             {"name": "weapon3", "image" : weapon3_image}] + [None] * 6     
    selected_weapon = 0
    selected_slot = 0
    chat_input = ""
    chat_log = []
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
    moving = False
    move_x = 0
    move_y = 0
    angle = 0
    knockback = 0
    death = pg.image.load('dead.png').convert()
    max_health = 100
    current_health = 100
    granade_range = 200
    items = []
    BLACK = (0, 0, 0)
    move_offset = (0, 0)
    world_offset = (0, 0)
    tmx_data = pytmx.load_pygame("c:/python_game/python-/map/map.tmx")  # <<< your TMX file here
    collidable_tiles = get_collidable_tiles(tmx_data)  # Get collidable tile coordinates
    kd_tree, pos_to_tile = build_collision_kdtree(collidable_tiles)
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
    thread_shooting = threading.Thread(target=shoot, args=(weapons, players_sprites, bullet_sprite, screen, my_player))
    thread_shooting.daemon = True
    thread_shooting.start()

    thread_bomb = threading.Thread(target=bomb, args=(players_sprites, screen, RED, granade_range, my_player, Socket))
    thread_bomb.daemon = True
    thread_bomb.start()
    
    thread_chat = threading.Thread(target=chat_sync_loop, args=(Socket, chat_log))
    thread_chat.daemon = True
    thread_chat.start()
    # thread_movement.start()
    while running:  
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if pg.K_1 <= event.key <= pg.K_3:
                    selected_weapon = event.key - pg.K_1
                    selected_slot = event.key - pg.K_1
                    print("Selected slot:", selected_weapon)
                elif pg.K_4 <= event.key <= pg.K_9:
                    selected_slot = event.key - pg.K_1
                    print("Selected slot:", selected_slot)
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                shared_data['fire'] = True
            elif event.type == pg.MOUSEMOTION:
                mouse = pg.mouse.get_pos()
                if mouse[0] == 500 or chat_input_active:
                    if mouse[1] == 325 or chat_input_active:
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

        # Check for collisions with nearby collision rects
        #print(f"Here pressed {keys}")
        #res = check_tile_collision(my_player, collidable_tiles, tile_width, tile_height)
        #print("Finished")
        #print(res)
                
            if event.type == pg.KEYDOWN:        
                if chat_input_active:
                    if event.key == pg.K_RETURN:
                        if chat_input.strip():
                            Socket.recvCHAT()
                            Socket.sendCHAT(chat_input)
                        chat_input = ""
                        chat_input_active = False
                    elif event.key == pg.K_ESCAPE:
                        chat_input = ""  # Clear input without sending
                        chat_input_active = False
                    elif event.key == pg.K_BACKSPACE:
                            chat_input = chat_input[:-1]
                    else:
                            chat_input += event.unicode
                else:
                    if event.key == pg.K_t:
                        chat_input_active = True

    # Movement only if not typing in chat
        if not chat_input_active:
            keys = pg.key.get_pressed()
            my_sprite = my_player['x'], my_player['y'], my_player['width'], my_player['height']
            my_sprite = pg.Rect(my_sprite)
            if knockback == 0:
                if keys[pg.K_w]:
                    if my_sprite.y > -270:
                        my_player['y'] -= 15
                        move_y = 15
                if keys[pg.K_s]:
                    if my_sprite.y < 21150:
                        my_player['y'] += 15
                        move_y = -15
                if keys[pg.K_a]:
                    if my_sprite.x > -400:
                        my_player['x'] -= 15
                        move_x = 15
                if keys[pg.K_d]:
                    if my_sprite.x < 23450:
                        my_player['x'] += 15
                        move_x = -15
                        
                if keys[pg.K_p] and selected_slot >= 3 and hotbar[selected_slot] is not None:
                    apply_item_effect(hotbar[selected_slot], my_player, weapons, shared_data, obj) 
                    hotbar[selected_slot] = None  # Remove item after use 
                    
                             
                if obj.check_collision_nearby(my_sprite, kd_tree, pos_to_tile, radius=80):
                        move_x = -move_x
                        move_y = -move_y
                        knockback = 8
                
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
            #new_msgs = Socket.recvCHAT()
            if not chat_input_active:
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
        
        obj.print_players(players_sprites, players, angle, selected_weapon)
        clock.tick(60)
        check_item_collision(my_player, items, weapons, shared_data, obj, hotbar, selected_slot)
        fps = clock.get_fps()                
        fps_text = font_fps.render(f"FPS: {fps:.2f}", True, (255, 0, 0))
        if chat_input_active == False:
            screen.blit(fps_text, (10, 10))
        draw_health_bar(screen, 10, 45, my_player['hp'], max_health)
        if chat_input_active:
            draw_chat_box(screen, font_chat, chat_log, chat_input, chat_input_active)           
        draw_hotbar(screen, selected_slot, hotbar)
        ammo_text = font_fps.render(f"Ammo: {weapons[selected_weapon]['ammo']}", True, (255, 0, 0))
        screen.blit(ammo_text, (10, 80))  # top-left corner
        pg.display.flip()
    pg.quit()


run_game()
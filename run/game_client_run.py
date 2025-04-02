import pygame as pg
import json
import Pmodel1
import ClientSocket
import time
import pytmx
import math
import sys
import os
import time


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

    powerup_cooldown = 10  # Cooldown duration in seconds
    last_powerup_use_time = 0  # Time when powerup was last used
    screen = pg.display.set_mode((1000, 650))
    clock = pg.time.Clock()
    font = pg.font.Font(None, 36)
    my_player = {'x': 400, 'y': 500, 'width': 20, 'height': 20, 'id': 0,'hp':100}
    players = [
        {"x": 300, "y": 200, "width": 20, "height": 20, "id": 1},
        {"x": 300, "y": 400, "width": 20, "height": 20, "id": 2},
        {"x": 700, "y": 500, "width": 20, "height": 20, "id": 3}
    ]
    used_weapon = 2
    weapons = [
        {"damage": 25, "range": 10000, 'bulet_speed': 40, 'ammo': 50, 'weapon_id': 1},
        {"damage": 20, "range": 70000, 'bulet_speed': 50, 'ammo': 20, 'weapon_id': 2},
        {"damage": 15, "range": 120000, 'bulet_speed': 70, 'ammo': 7, 'weapon_id': 3}

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
    # my_sprite = Pmodel1.Player.convert_to_sprite(my_player['x'], my_player['y'], my_player['height'], my_player['width'],my_player['id'])
    # players_sprites = [
    #   Pmodel1.Player.convert_to_sprite(player['x'], player['y'], player['height'], player['width'], player['id'])
    #  for player in players
    # ]
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
        my_sprite,
        weapons)
  # Create PlayerSprite objects for each player
    # players_sprites = [Pmodel1.PlayerSprite(player['x'], player['y'], player['width'], player['height']) for player in players]
    # my_player_sprite = Pmodel1.PlayerSprite(my_player['x'], my_player['y'], my_player['width'], my_player['height'])
    #--------------------------------------------------------------------------------
    Socket = ClientSocket.ClientServer()
    Socket.connect()
    # Replace the hardcoded players list with data from the server
    players = Socket.requestDATA()
    # print (players)
    running = True
    h=None
    g=None
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                target_pos = pg.mouse.get_pos()
                move_offset = (target_pos[0] - 500, target_pos[1] - 325)
                moving = True
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                if weapons[used_weapon]['ammo']==0:
                    print ('out of ammo')
                else:
                    startpos1=0
                    startpos2=0
                    hit=False
                    range1=1
                    weapons[used_weapon]['ammo'] -= 1
                    shot_offset = list(pg.mouse.get_pos())
                    shot_offset[0] -= 500
                    shot_offset[1] = 325 - shot_offset[1]
                    added_dis=range1*weapons[used_weapon]['bulet_speed']
                    while abs(range1) < weapons[used_weapon]['range']-1 and not hit:
                        range1+=added_dis+range1*0.002
                        # direction = (0- (325 - shot_offset[1])) / (0- (shot_offset[0] - 500))
                        try:
                            direction = (0 - shot_offset[1]) / (0 - shot_offset[0])
                            shot_offset[0] = (shot_offset[0] / abs(shot_offset[0])) * math.sqrt(
                                range1 / (direction * direction + 1))
                            shot_offset[1] = direction * shot_offset[0]  # shot offset is the x,y of the max distance of shot
                        except ZeroDivisionError:
                            shot_offset[1]=(shot_offset[1] / abs(shot_offset[1])*math.sqrt(range1))
                            shot_offset[0]=0
                        endpos1=shot_offset[0]+500
                        endpos2=325-shot_offset[1]
                        #startpos1=(shot_offset[0]*3)/4
                        #startpos2=(shot_offset[1]*3)/4
                        #startpos1+=500
                        #startpos2=325-startpos2
                        #print (endpos1,endpos2,startpos1,startpos2)
                        #-------------------------------------------------------------
                        # Create a surface to draw the line
                       # line = LineSprite((100, 150), (400, 300), (0, 255, 0), 5)
                        pg.draw.line(screen,RED,(500,325), (endpos1,endpos2), width=5)
                        # pg.draw.circle(screen,RED,(500,325),granade_range, width=0)
                        pg.display.flip()
                        for i in range (0,players_sprites.__len__()):
                            if players_sprites[i]['rect'].clipline((500,325),(endpos1,endpos2)):
                                print("hit" + " "+str(i)+' '+'with weapon'+ ' '+str(used_weapon+1))
                                hit =True

            elif event.type == pg.KEYDOWN:  # Check if a key was pressed
                if event.key == pg.K_1:
                    used_weapon=0
                elif event.key == pg.K_2:
                    used_weapon=1 
                elif event.key == pg.K_3:
                    used_weapon=2
                # obj.shoot(used_weapon)
                elif event.key == pg.K_q:
                    big_boom_boom(players,screen,RED,granade_range)
                # Powerups and Items activation
                elif event.key == pg.K_w:
                    current_time = time.time()
                    if current_time - last_powerup_use_time >= powerup_cooldown:
                        obj.activate_invulnerability(5)  # Activate invulnerability
                        last_powerup_use_time = current_time  # Update last used time
                        print("Vulnerability activated")
                    else:
                        time_left = powerup_cooldown - (current_time - last_powerup_use_time)
                        print(f"Powerup on cooldown. {time_left:.2f} seconds left.")

                elif event.key == pg.K_4:
                    obj.heal(50)  # Heal with medkit
                    print("Restored 50 health")
                elif event.key == pg.K_5:
                    obj.add_ammo(weapon_id=used_weapon+1, amount=10)  # Add ammo
                    print("Added 10 ammo to weapon")
                elif event.key == pg.K_6:
                    obj.add_ammo(weapon_id=used_weapon+1, amount=-10)
                    print("Removed 10 ammo from weapon")
                elif event.key == pg.K_7:
                    obj.heal(-50) #remove health
                    print("Removed 50 health")
                       
        # Stop movement in the direction of the collisio
        # Update player position
        #players = Socket.run_conn(obj.convert_to_json())
        #---------------------------------------------------------------------------
        #updated_players = None#Socket.run_conn(obj.convert_to_json())
        #for player in updated_players:
        #    for key in player.keys():
        #        if player[key] is None:
        #            continue
        #        players[player['id']][key]=player[key]
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
        # for i in range(0,players.__len__()-1):
        # players [i]['x']+=1
        # players [i]['y']+=1
        # players_sprites[i]['rect'].x=players[i]['x']
        # players_sprites[i]['rect'].y=players[i]['y']
        # print(players)
        # print (my_player)
        # if colision_id[0] == 0:
        for player in players_sprites:
            if my_sprite['rect'].colliderect(player['rect']):  # Check collision using rect
                move_offset = (500 - player['rect'].x, player['rect'].y - 325)
                target_pos = (500, 325)
                moving = True
                tp = 500
                tp2 = 325
                # Apply knockback based on movement direction
                if move_offset[0] > 0:  # Moving right
                    tp = 465  # Knockback to the left)
                elif move_offset[0] < 0:  # left
                    tp = 535  # Knockback to the right
                if move_offset[1] > 0:  # Moving down
                    tp2 = 290  # Knockback upward
                elif move_offset[1] < 0:  # Moving up
                    tp2 = 360  # Knockback downward
                move_offset = (tp - 500, tp2 - 325)
        moving, move_offset, x, y = obj.move(players_sprites, acceleration, move_offset, moving)
        time.sleep(0.0001)
        for i in range(0, players.__len__() - 1):
            players[i]['x'] = players_sprites[i]['rect'].x
            players[i]['y'] = players_sprites[i]['rect'].y
        obj.update_players_sprites(players, players_sprites)

        obj.update() # Add this line here
        
        screen.fill(BLACK)

        # Render Health and ammo text on the map
        health_text = font.render(f"Health: {obj.health}", True, (255,255,255)) # White color
        ammo_text = font.render(f"Ammo: {weapons[used_weapon]['ammo']}", True, (255, 255, 255))

        screen.blit(health_text, (10, 10))  # Position at the top-left corner
        screen.blit(ammo_text, (10, 50))  # Position below the health text

        obj.print_players(players_sprites, screen)
        pg.display.flip()

        world_offset = (500 - my_player['x'], 325 - my_player['y'])
        # draw_map(screen, tmx_data, world_offset)
        obj.print_players(players_sprites, screen)
        pg.display.flip()
        clock.tick(60)

    pg.quit()


run_game()
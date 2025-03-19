import pygame as pg
import json
import tile
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
                
                    


def run_game():
    pg.init()

    screen = pg.display.set_mode((1000, 650))
    clock = pg.time.Clock()
    my_player = {'x': 400, 'y': 400, 'width': 20, 'height': 20, 'id': 0}
    players = [
        # {"x": 300, "y": 200, "width": 20, "height": 20, "id": 1},
        # {"x": 400, "y": 300, "width": 20, "height": 20, "id": 2},
        # {"x": 700, "y": 500, "width": 20, "height": 20, "id": 3}
    ]
    used_weapon = 2
    weapons = [
        {"damage": 25, "range": 50, 'bulet_speed': 0.2, 'ammo': 50, 'weapon_id': 1},
        {"damage": 20, "range": 100, 'bulet_speed': 0.3, 'ammo': 20, 'weapon_id': 2},
        {"damage": 15, "range": 1900, 'bulet_speed': 0.5, 'ammo': 7, 'weapon_id': 3}

    ]
    BLACK = (0, 0, 0)
    move_offset = (0, 0)
    world_offset = (0, 0)
<<<<<<< HEAD

    # Load and pre-render the map
    tmx_data = load_tmx_map("c:/networks/webroot/map.tmx")


    if not tmx_data:
        return  # Exit if map loading fails

=======
    tmx_data = load_tmx_map("c:/webroot/map.tmx")
>>>>>>> 554a4940934236e93666f09d3c4e89109c5584f2
    map_surface = render_map(tmx_data)  # Pre-render the map

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
        100,
        0.1,
        players,
        False,
        (0, 0),
        0,
        screen,
        players_sprites,
        my_sprite
<<<<<<< HEAD
    )

    # Initialize socket connection
    #Socket = ClientSocket.ClientServer()
    #Socket.connect()

=======
    )  # Create PlayerSprite objects for each player
    # players_sprites = [Pmodel1.PlayerSprite(player['x'], player['y'], player['width'], player['height']) for player in players]
    # my_player_sprite = Pmodel1.PlayerSprite(my_player['x'], my_player['y'], my_player['width'], my_player['height'])
    #Socket = ClientSocket.ClientServer()
    #Socket.connect()
    #players = Socket.run_conn(obj.convert_to_json())
    # print (players)
>>>>>>> 554a4940934236e93666f09d3c4e89109c5584f2
    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                target_pos = pg.mouse.get_pos()
                move_offset = (target_pos[0] - 500, target_pos[1] - 325)
                moving = True
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 3:
                weapons[used_weapon]['ammo'] -= 1
                shot_offset = list(pg.mouse.get_pos())
                shot_offset[0] -= 500
                shot_offset[1] = 325 - shot_offset[1]
                #direction = (0- (325 - shot_offset[1])) / (0- (shot_offset[0] - 500))
                direction = (0 - shot_offset[1]) / (0 - shot_offset[0])
                shot_offset[0] = (shot_offset[0] / abs(shot_offset[0])) * math.sqrt(
                    weapons[used_weapon]['range'] / (direction * direction + 1))
                shot_offset[1] = direction * shot_offset[0]  # shot offset is the x,y of the max distance of shot
                # Create a surface to draw the line
                image = pg.Surface((1, 1), pg.SRCALPHA)  # Transparent background
                rect = image.get_rect(topleft=(min(shot_offset[0] + 500, 500), min(325 - shot_offset[1], 325)))
                print(rect)
                # line = LineSprite((100, 150), (400, 300), (0, 255, 0), 5)
                print(f"Start: {shot_offset[0] + 500, 325 - shot_offset[1]}, End: {500, 325}")

                # obj.shoot(used_weapon)
        collisions = []
        # Stop movement in the direction of the collisio
        # Update player position

<<<<<<< HEAD
        # Update world offset so the map moves with the player
        world_offset = (500 - x, 325 - y)

        # Send player position to the server and get updated player data
        #players = Socket.run_conn(obj.convert_to_json())
        players = [
            {"x": 300, "y": 300, "width": 20, "height": 20, "id": 2},
            {"x": 200, "y": 200, "width": 20, "height": 20, "id": 3},
        ]
        # Update other players' positions relative to the world offset
=======
        #players = Socket.run_conn(obj.convert_to_json())
>>>>>>> 554a4940934236e93666f09d3c4e89109c5584f2
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
                elif move_offset[0] < 0:  # Moving left
                    tp = 535  # Knockback to the right
                if move_offset[1] > 0:  # Moving down
                    tp2 = 290  # Knockback upward
                elif move_offset[1] < 0:  # Moving up
                    tp2 = 360  # Knockback downward
                move_offset = (tp - 500, tp2 - 325)
        moving, move_offset, x, y = obj.move(players_sprites, acceleration, move_offset, moving)
        for i in range(0, players.__len__() - 1):
            players[i]['x'] = players_sprites[i]['rect'].x
            players[i]['y'] = players_sprites[i]['rect'].y
        obj.update_players_sprites(players, players_sprites)
        #screen.fill(BLACK)
        world_offset = (500 - x, 325 - y)
        #draw_map(screen, tmx_data, world_offset)
        screen.blit(map_surface, world_offset)
        obj.print_players(players_sprites, screen)
        pg.display.flip()
        clock.tick(60)

    pg.quit()


run_game()


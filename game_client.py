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


def draw_map(screen, tmx_data, world_offset):
    """Draw the TMX map with an offset to simulate camera movement."""
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    map_surface.blit(tile, (x * tmx_data.tilewidth, y * tmx_data.tileheight))
    
    return map_surface


def run_game():
    pg.init()

    # Screen and game settings
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
    tmx_data = load_tmx_map("c:/webroot/map.tmx")
    acceleration = 0.05
    moving = False

    # Create player sprite
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

    # Initialize player object
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
    )  # Create PlayerSprite objects for each player
    # players_sprites = [Pmodel1.PlayerSprite(player['x'], player['y'], player['width'], player['height']) for player in players]
    # my_player_sprite = Pmodel1.PlayerSprite(my_player['x'], my_player['y'], my_player['width'], my_player['height'])
    #Socket = ClientSocket.ClientServer()
    #Socket.connect()

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

        #players = Socket.run_conn(obj.convert_to_json())
        for player in players:
            player['x'] = player['x'] - my_player['x'] + 500
            player['y'] = player['y'] - my_player['y'] + 325

        # Update player sprites
        players_sprites = [
            {
                "image": pg.Surface((player["width"], player["height"])),
                "rect": pg.Rect(player["x"], player["y"], player["width"], player["height"]),
            }
            for player in players
        ]
        obj.update_players_sprites(players, players_sprites)

        # Render the frame
        screen.fill(BLACK)
        world_offset = (500 - x, 325 - y)
        draw_map(screen, tmx_data, world_offset)
        obj.print_players(players_sprites, screen)
        pg.display.flip()
        clock.tick(60)

    pg.quit()


run_game()

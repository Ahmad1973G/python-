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
    """Render the TMX map onto a surface once to improve performance."""
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

    # Screen settings
    screen = pg.display.set_mode((1000, 650))
    clock = pg.time.Clock()
    
    my_player = {'x': 400, 'y': 400, 'width': 20, 'height': 20, 'id': 0}
    players = []

    used_weapon = 2
    weapons = [
        {"damage": 25, "range": 50, 'bulet_speed': 0.2, 'ammo': 50, 'weapon_id': 1},
        {"damage": 20, "range": 100, 'bulet_speed': 0.3, 'ammo': 20, 'weapon_id': 2},
        {"damage": 15, "range": 1900, 'bulet_speed': 0.5, 'ammo': 7, 'weapon_id': 3}
    ]

    BLACK = (0, 0, 0)
    
    move_offset = (0, 0)
    world_offset = (0, 0)

    # Load and pre-render the map
    tmx_data = load_tmx_map("c:/webroot/map.tmx")
    if not tmx_data:
        return  # Exit if map loading fails

    map_surface = render_map(tmx_data)  # Pre-render the map

    acceleration = 0.05
    moving = False

    # Create player sprite
    my_sprite = {
        "image": pg.Surface((my_player["width"], my_player["height"])),
        "rect": pg.Rect(500, 325, my_player["width"], my_player["height"]),
    }

    players_sprites = []

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
    )

    # Initialize socket connection
    Socket = ClientSocket.ClientServer()
    Socket.connect()

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

        # Update movement
        moving, move_offset, x, y = obj.move(players_sprites, acceleration, move_offset, moving)

        # Update world offset so the map moves with the player
        world_offset = (500 - x, 325 - y)

        # Send player position to the server and get updated player data
        players = Socket.run_conn(obj.convert_to_json())
        updated_players = Socket.run_conn(obj.convert_to_json())
        for player in updated_players:
            for key in player.keys():
                if player[key] is None:
                    continue
                players[player['id']][key] = player[key]

        # Update player sprites
        players_sprites = [
            {
                "image": pg.Surface((player["width"], player["height"])),
                "rect": pg.Rect(player["x"] - my_player['x'] + 500, 
                                player["y"] - my_player['y'] + 325, 
                                player["width"], player["height"]),
            }
            for player in players
        ]

        obj.update_players_sprites(players, players_sprites)

        # Collision Handling
        for player in players_sprites:
            if my_sprite['rect'].colliderect(player['rect']):  # Check collision
                move_offset = (500 - player['rect'].x, player['rect'].y - 325)
                moving = True
                
                # Apply knockback effect
                if move_offset[0] > 0:  # Moving right
                    move_offset = (-20, move_offset[1])
                elif move_offset[0] < 0:  # Moving left
                    move_offset = (20, move_offset[1])
                if move_offset[1] > 0:  # Moving down
                    move_offset = (move_offset[0], -20)
                elif move_offset[1] < 0:  # Moving up
                    move_offset = (move_offset[0], 20)

        # Render the frame
        screen.fill(BLACK)
        screen.blit(map_surface, world_offset)  # Efficient map rendering
        obj.print_players(players_sprites, screen)  # Draw other players

        pg.display.flip()
        clock.tick(60)

    pg.quit()


run_game()

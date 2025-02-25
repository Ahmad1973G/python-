import pygame as pg

import json





def main():

    pg.init()
    screen = pg.display.set_mode((1000, 650))
    clock = pg.time.Clock()
    image = pg.Surface((30, 30))
    image.fill(pg.Color('dodgerblue1'))
    x, y = 300, 200  # Actual position.
    rect = image.get_rect(center=(x, y))  # Blit position.

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return

        mouse_pos = pg.mouse.get_pos()
        # x and y distances to the target.
        run = (mouse_pos[0] - x) * 0.1  # Scale it to the desired length.
        rise = (mouse_pos[1] - y) * 0.1
        # Update the position.
        if event.type == pg.MOUSEBUTTONDOWN \
        and event.button == 1:
            x += run
            y += rise
            rect.center = x, y

        screen.fill((30, 30, 30))
        screen.blit(image, rect)

        pg.display.flip()
        clock.tick(60)


    
def print_players(players_list, client_loc):
    screen = pg.display.set_mode((1000, 650))
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
        for player in players_list:
            if player['id'] != client_loc['id']:
                image = pg.Surface((player['width'], player['height']))
                image.fill(pg.Color('red'))
                rect = image.get_rect(center=(player['x'], player['y']))
                screen.blit(image, rect)
                pg.display.flip()
            
        else:
            image = pg.Surface((client_loc['width'], client_loc['height']))
            image.fill(pg.Color('blue'))
            rect = image.get_rect(center=(client_loc['x'], client_loc['y']))
            screen.blit(image, rect)
            pg.display.flip()
            
    
if __name__ == '__main__':
    main_player = {"x": 500, "y": 325, "width": 20, "height": 20, "id": 0}  # Main player is always in the middle.
    players = [
        {"x": 600, "y": 400, "width": 20, "height": 20, "id": 1},
        {"x": 400, "y": 300, "width": 20, "height": 20, "id": 2},
        {"x": 700, "y": 500, "width": 20, "height": 20, "id": 3}
    ]
    print_players(players, main_player)
    main()
    pg.quit()
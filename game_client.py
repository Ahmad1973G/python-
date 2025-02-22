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


if __name__ == '__main__':
    main()
    pg.quit()
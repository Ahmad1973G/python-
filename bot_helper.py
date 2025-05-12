import bots
import pygame as pg
def run():
    # Initialize the game
    pg.init()
    screen = pg.display.set_mode((1000,650))
    clock = pg.time.Clock()

    # Create a bot instance
    bot = bots.Bots(400,400,False,1,1,screen)

    # Main game loop
    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.MOUSEBUTTONDOWN:
                mouse = pg.mouse.get_pos()
                bot.SeNdTArGeT(mouse[0], mouse[1])

        # Draw the bot

        clock.tick(60)

    pg.quit()
if __name__ == "__main__":
    run()
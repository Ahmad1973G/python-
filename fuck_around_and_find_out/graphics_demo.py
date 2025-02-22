

import pygame   # type: ignore

WINDOW_WIDTH = 256
WINDOW_HEIGHT = 256
pygame.init()
size = (WINDOW_WIDTH, WINDOW_HEIGHT)
screen = pygame.display.set_mode(size)
IMAGE = 'pyramid.png'
img = pygame.image.load(IMAGE)
screen.blit(img, (0, 0))
pygame.display.flip()
finish = False
while not finish:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            finish = True

pygame.quit()
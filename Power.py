import pygame

class Power:
    def __init__(self, range, damage, radius):
        self.range = range
        self.damage = damage
        self.radius = radius

    def UsePower1(self, player, duration):
        """
        SuperSpeed: Doubles the player's speed for a specified duration.
        Args:
        player (Player): The player object to apply the speed boost to.
        duration (int): The duration of the speed boost in milliseconds.
        """
        original_speed = player.speed
        player.speed *= 2  # Double the speed
        
        pygame.time.set_timer(pygame.USEREVENT, duration)  # Set a timer for the duration
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT:
                    player.speed = original_speed  # Reset speed to original value
                    return  # End the power-up effect
            
            # Your game loop code here
            pygame.time.delay(10)  # Small delay to prevent the loop from running too fast

    def usePower2(self):
        pass

    def usePower3(self):
        pass

    def usePower4(self):
        pass

    def usePower5(self):
        pass

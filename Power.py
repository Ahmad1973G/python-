import pygame

class Power:
    def __init__(self, range, damage, radius): # this is useless for now
        self.range = range
        self.damage = damage
        self.radius = radius

    def UsePower1(self, player, duration):
        """
        SuperSpeed: Doubles the player's speed for a few seconds.
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

    def UsePower2(self, player, duration):
        """
        Shield: Makes the player invulnerable for a few seconds
        
        Args:
        player (Player): The player object to apply the shield to.
        duration (int): The duration of the invulnerability in milliseconds.
        """
        # add invulnerability
        
        pygame.time.set_timer(pygame.USEREVENT, duration)  # Set a timer for the duration
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT:
                      # Remove invulnerability
                    return  # End the power-up effect
            
            # Your game loop code here
            pygame.time.delay(10)  # Small delay to prevent the loop from running too fast

    def UsePower3(self, player):
        """
        Replenish: Restores the player's health and ammo to maximum.
        
        Args:
        player (Player): The player object to replenish health and ammo for.
        """
        player.health = player.max_health
        player.ammo = player.max_ammo

    def UsePower4(self):
        pass

    def UsePower5(self):
        pass

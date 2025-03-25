import pygame

class Power:
    def __init__(self):
        pass

    def power1(self, player):
        """Speed boost: Doubles the player's speed for 5 seconds."""
        original_speed = player.speed
        player.speed *= 2  # Double the speed
        pygame.time.set_timer(pygame.USEREVENT + 1, 5000)  # Set a timer for 5 seconds

        def reset_speed():
            player.speed = original_speed  # Reset speed to original value
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # Stop the timer

        player.event_handlers[pygame.USEREVENT + 1] = reset_speed

    def power2(self, player):
        """Shield: Makes the player invulnerable for 5 seconds."""
        player.invulnerable = True  # Set invulnerability
        pygame.time.set_timer(pygame.USEREVENT + 2, 5000)  # Set a timer for 5 seconds

        def disable_shield():
            player.invulnerable = False  # Remove invulnerability
            pygame.time.set_timer(pygame.USEREVENT + 2, 0)  # Stop the timer

        player.event_handlers[pygame.USEREVENT + 2] = disable_shield

    def power3(self, player):
        """Regeneration: Adds 5 HP every second for 5 seconds."""
        def regenerate():
            if player.health < player.max_health:
                player.health = min(player.health + 5, player.max_health)  # Add 5 HP
            player.regen_ticks += 1
            if player.regen_ticks >= 5:  # Stop after 5 ticks
                pygame.time.set_timer(pygame.USEREVENT + 3, 0)  # Stop the timer

        player.regen_ticks = 0
        pygame.time.set_timer(pygame.USEREVENT + 3, 1000)  # Set a timer for 1 second intervals
        player.event_handlers[pygame.USEREVENT + 3] = regenerate
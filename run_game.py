#!/usr/bin/env python3
import os
import sys

# Import missing modules if they exist in the same directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main game function
from game_client import run_game

if __name__ == "__main__":
    # Run the game
    run_game()
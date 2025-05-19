#!/bin/bash

# Start virtual framebuffer
Xvfb :99 -screen 0 1024x768x16 &

# Start VNC server
x11vnc -display :99 -forever -nopw -shared &

# Run the game
python run_game.py
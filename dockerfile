FROM python:3.9-slim

# Install dependencies for pygame, X11, and other necessary libraries
RUN apt-get update && apt-get install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    python3-dev \
    python3-numpy \
    python3-tk \
    x11-xserver-utils \
    xvfb \
    xorg \
    libx11-dev \
    libxext-dev \
    libasound2-dev \
    libpulse-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all game files
COPY . .

# Set up display environment variable
ENV DISPLAY=:0

# Create a script to run the game with Xvfb
RUN echo '#!/bin/bash\nXvfb :0 -screen 0 1024x768x24 &\npython game_client.py' > /app/start_game.sh && \
    chmod +x /app/start_game.sh

# Command to run when container starts
CMD ["/app/start_game.sh"]
FROM python:3.8

# Install required system dependencies for pygame and other libraries
RUN apt-get update && apt-get install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    libjpeg-dev \
    libtiff-dev \
    libwebp-dev \
    libx11-dev \
    libxcursor-dev \
    libxext-dev \
    libxi-dev \
    libxinerama-dev \
    libxrandr-dev \
    libxss-dev \
    libxt-dev \
    libxxf86vm-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy required Python files
COPY game_client.py Pmodel1.py ClientSocket.py ./

# Copy game assets
COPY *.png ./
COPY map.tmx ./

# Install Python dependencies
RUN pip install pygame pytmx

# Set display environment variable for pygame
ENV SDL_VIDEODRIVER=x11

# Run the game client
CMD ["python", "./game_client.py"]
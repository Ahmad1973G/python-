FROM python:3.9

# Install X11 dependencies and other required packages
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    python3-tk \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Install Python dependencies directly
RUN pip install --no-cache-dir pygame pytmx scipy numpy python-dotenv

# Copy the game files
COPY . .

# Set up the virtual display
ENV DISPLAY=:99

# Create a simple entrypoint script
RUN echo '#!/bin/bash\nXvfb :99 -screen 0 1024x768x16 &\nx11vnc -display :99 -forever -nopw -shared &\npython paste.py' > /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose the VNC port
EXPOSE 5900

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]
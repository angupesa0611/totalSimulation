FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb libgl1 libgl1-mesa-dri libglu1-mesa \
    libxrender1 libxcursor1 libxft2 libxinerama1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir vtk numpy matplotlib celery[redis]==5.4.0 redis==5.2.1

WORKDIR /app
COPY . .

ENV DISPLAY=:99

# Start Xvfb (no-auth) then Celery; -ac disables X access control so
# all forked Celery workers can connect to the virtual display.
CMD Xvfb :99 -screen 0 1280x1024x24 -ac +extension GLX +render -noreset & \
    sleep 1 && \
    celery -A worker worker --queues=rendering --concurrency=1 --loglevel=info

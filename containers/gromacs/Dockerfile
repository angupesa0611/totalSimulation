FROM gromacs/gromacs:latest

WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install MDAnalysis for trajectory conversion + Celery
RUN pip3 install --no-cache-dir --break-system-packages \
    celery[redis]==5.4.0 \
    redis==5.2.1 \
    MDAnalysis==2.8.0 \
    numpy==1.26.4

COPY . .

CMD ["python3", "-m", "celery", "-A", "worker", "worker", "--queues=molecular-gmx", "--concurrency=1", "--loglevel=info"]

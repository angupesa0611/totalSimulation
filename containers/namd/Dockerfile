# Stage 1: Extract NAMD binary from pre-built image
FROM openeuler/namd:latest AS namd-source

# Stage 2: Build the worker image
FROM ubuntu:24.04

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy NAMD binary from the pre-built image
COPY --from=namd-source /opt/namd/Linux-x86_64-g++.arch/namd3 /usr/local/bin/namd3
COPY --from=namd-source /opt/namd/Linux-x86_64-g++.arch/charmrun /usr/local/bin/charmrun
RUN chmod +x /usr/local/bin/namd3 /usr/local/bin/charmrun

# Install MDAnalysis for trajectory conversion + Celery
RUN pip3 install --no-cache-dir --break-system-packages \
    celery[redis]==5.4.0 \
    redis==5.2.1 \
    MDAnalysis==2.8.0 \
    numpy==1.26.4

COPY . .

CMD ["python3", "-m", "celery", "-A", "worker", "worker", "--queues=molecular-namd", "--concurrency=1", "--loglevel=info"]

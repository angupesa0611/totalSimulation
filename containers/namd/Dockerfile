FROM ubuntu:22.04

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev \
    wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install NAMD (multicore version)
RUN wget -q https://www.ks.uiuc.edu/Research/namd/3.0/download/946183/NAMD_3.0_Linux-x86_64-multicore.tar.gz \
    -O /tmp/namd.tar.gz \
    && tar xzf /tmp/namd.tar.gz -C /opt/ \
    && ln -s /opt/NAMD_3.0_Linux-x86_64-multicore /opt/namd \
    && rm /tmp/namd.tar.gz \
    || echo "NAMD download requires registration; place binary manually at /opt/namd/namd3"

ENV PATH="/opt/namd:${PATH}"

# Install MDAnalysis for trajectory conversion + Celery
RUN pip3 install --no-cache-dir --break-system-packages \
    celery[redis]==5.4.0 \
    redis==5.2.1 \
    MDAnalysis==2.8.0 \
    numpy==1.26.4

COPY . .

CMD ["python3", "-m", "celery", "-A", "worker", "worker", "--queues=molecular-namd", "--concurrency=1", "--loglevel=info"]

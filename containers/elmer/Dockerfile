FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install ElmerFEM via PPA and Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common gpg gpg-agent \
    && add-apt-repository -y ppa:elmer-csc-ubuntu/elmer-csc-ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    elmerfem-csc \
    python3 \
    python3-pip \
    python3-numpy \
    && rm -rf /var/lib/apt/lists/*

# Install Celery + Redis
RUN pip3 install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=continuum-elmer", "--concurrency=1", "--loglevel=info"]

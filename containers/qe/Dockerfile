FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    quantum-espresso \
    python3 python3-pip python3-numpy \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    celery[redis]==5.4.0 \
    redis==5.2.1 \
    ase==3.23.0

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=materials-qe", "--concurrency=1", "--loglevel=info"]

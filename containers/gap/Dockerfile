FROM ubuntu:22.04

RUN apt-get update && apt-get install -y gap python3 python3-pip python3-numpy && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1

WORKDIR /app
COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=math-gap", "--concurrency=1", "--loglevel=info"]

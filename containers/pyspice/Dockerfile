FROM python:3.11-slim

RUN apt-get update && apt-get install -y ngspice && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir PySpice celery[redis]==5.4.0 redis==5.2.1 numpy

WORKDIR /app
COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=circuits-spice", "--concurrency=1", "--loglevel=info"]

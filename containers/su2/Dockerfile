FROM su2code/su2-build:latest

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip python3-numpy \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages celery[redis]==5.4.0 redis==5.2.1

WORKDIR /app
COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=cfd-su2", "--concurrency=1", "--loglevel=info"]

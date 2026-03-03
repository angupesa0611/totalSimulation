FROM nest/nest-simulator:3.8

USER root

WORKDIR /app

# Install Celery + Redis
RUN pip3 install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1 numpy

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=neuro-nest", "--concurrency=1", "--loglevel=info"]

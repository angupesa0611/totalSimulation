FROM dolfinx/dolfinx:stable

WORKDIR /app

# Install Celery + Redis
RUN pip install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=continuum-fenics", "--concurrency=1", "--loglevel=info"]

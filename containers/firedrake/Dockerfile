FROM firedrakeproject/firedrake:latest

WORKDIR /app

RUN pip install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=continuum-firedrake", "--concurrency=1", "--loglevel=info"]

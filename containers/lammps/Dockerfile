FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    lammps \
    celery[redis]==5.4.0 \
    redis==5.2.1 \
    numpy

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=materials-lammps", "--concurrency=1", "--loglevel=info"]

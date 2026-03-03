FROM einsteintoolkit/et-notebook:latest

WORKDIR /app

RUN pip install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1 h5py numpy

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=astro-etk", "--concurrency=1", "--loglevel=info"]

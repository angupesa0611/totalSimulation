FROM einsteintoolkit/et-notebook:latest

USER root
WORKDIR /app

RUN pip install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1 h5py numpy

COPY . .

ENTRYPOINT []
CMD ["python3", "-m", "celery", "-A", "worker", "worker", "--queues=astro-etk", "--concurrency=1", "--loglevel=info"]

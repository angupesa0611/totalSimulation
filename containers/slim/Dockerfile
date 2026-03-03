FROM condaforge/miniforge3:latest
WORKDIR /app
RUN conda install -y -c conda-forge slim-simulator numpy && conda clean -afy
RUN pip install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1 tskit pyslim
COPY . .
CMD ["celery", "-A", "worker", "worker", "--queues=evolution-slim", "--concurrency=1", "--loglevel=info"]

FROM condaforge/miniforge3:latest
WORKDIR /app

# SU2 conda-forge only has py3.10 builds — pin Python first
RUN conda install -y python=3.10 && conda clean -afy
RUN conda install -y -c conda-forge su2 numpy && conda clean -afy

RUN pip install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=cfd-su2", "--concurrency=1", "--loglevel=info"]

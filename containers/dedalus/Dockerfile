FROM condaforge/miniforge3:latest

RUN conda install -y -c conda-forge dedalus numpy scipy h5py matplotlib && conda clean -afy
RUN pip install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1

WORKDIR /app
COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=spectral-pde", "--concurrency=1", "--loglevel=info"]

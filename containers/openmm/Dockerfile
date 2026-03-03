FROM condaforge/miniforge3:latest

WORKDIR /app

# Install OpenMM with CUDA support
RUN conda install -y -c conda-forge \
    openmm \
    cudatoolkit \
    pdbfixer \
    numpy \
    && conda clean -afy

# Install Celery + Redis
RUN pip install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=molecular", "--concurrency=1", "--loglevel=info"]

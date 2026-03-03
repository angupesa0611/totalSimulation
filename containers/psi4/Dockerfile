FROM condaforge/miniforge3:latest

WORKDIR /app

# Install Psi4 from conda-forge
RUN conda install -y -c conda-forge \
    psi4 \
    numpy \
    && conda clean -afy

# Install Celery + Redis
RUN pip install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=electronic-psi4", "--concurrency=2", "--loglevel=info"]

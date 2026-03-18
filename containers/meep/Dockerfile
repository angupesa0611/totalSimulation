FROM continuumio/miniconda3:latest

WORKDIR /app

# Install Meep (FDTD) from conda-forge
RUN conda install -y -c conda-forge \
    pymeep \
    numpy \
    h5py \
    matplotlib \
    && conda clean -afy

# Install Celery + Redis
RUN pip install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=em-meep", "--concurrency=1", "--loglevel=info"]

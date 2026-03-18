FROM condaforge/miniforge3:latest
WORKDIR /app

# Install GROMACS from conda-forge (avoids old Python in official image)
RUN conda install -y -c conda-forge gromacs numpy && conda clean -afy

RUN pip install --no-cache-dir \
    celery[redis]==5.4.0 \
    redis==5.2.1 \
    MDAnalysis==2.8.0

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=molecular-gmx", "--concurrency=1", "--loglevel=info"]

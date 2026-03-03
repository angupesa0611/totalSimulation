FROM condaforge/miniforge3:latest

WORKDIR /app

# Install OpenMM (CPU-only — GPU reserved for standalone OpenMM container)
RUN conda install -y -c conda-forge \
    openmm \
    numpy \
    && conda clean -afy

# Install PySCF + ASH + Celery
RUN pip install --no-cache-dir \
    pyscf==2.7.0 \
    ash-qm \
    celery[redis]==5.4.0 \
    redis==5.2.1

# Force OpenMM CPU platform
ENV OPENMM_DEFAULT_PLATFORM=CPU

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=qmmm", "--concurrency=1", "--loglevel=info"]

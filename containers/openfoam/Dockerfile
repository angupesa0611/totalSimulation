FROM openfoam/openfoam11-paraview510:latest

USER root
RUN apt-get update && apt-get install -y python3-pip python3-numpy && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1

WORKDIR /app
COPY . .

# Override base image's entrypoint but source OpenFOAM environment
ENTRYPOINT []
CMD ["bash", "-c", "source /opt/openfoam11/etc/bashrc && python3 -m celery -A worker worker --queues=cfd-foam --concurrency=1 --loglevel=info"]

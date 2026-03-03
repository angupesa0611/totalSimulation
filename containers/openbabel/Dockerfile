FROM python:3.11-slim

WORKDIR /app

# Install Open Babel system library + Python bindings
RUN apt-get update && apt-get install -y --no-install-recommends \
    openbabel \
    libopenbabel-dev \
    python3-openbabel \
    swig \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    openbabel-wheel==3.1.1.19 \
    celery[redis]==5.4.0 \
    redis==5.2.1 \
    numpy==1.26.4

COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=cheminformatics", "--concurrency=2", "--loglevel=info"]

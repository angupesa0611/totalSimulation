FROM ubuntu:22.04

RUN apt-get update && apt-get install -y curl git python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install elan (Lean 4 version manager)
RUN curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | \
    bash -s -- -y --default-toolchain leanprover/lean4:stable

ENV PATH="/root/.elan/bin:${PATH}"

RUN pip3 install --no-cache-dir celery[redis]==5.4.0 redis==5.2.1

WORKDIR /app
COPY . .

CMD ["celery", "-A", "worker", "worker", "--queues=math-lean", "--concurrency=1", "--loglevel=info"]

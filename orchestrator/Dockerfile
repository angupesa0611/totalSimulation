FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ pkg-config libpq-dev glpk-utils coinor-cbc coinor-libipopt-dev \
    libosmesa6-dev libgl1-mesa-dev libglu1-mesa libxcursor1 libxrandr2 libxinerama1 libxi6 \
    ngspice libngspice0-dev cmake make gap \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Build LAMMPS from source (serial mode, no MPI dependency)
RUN cd /tmp && \
    curl -fsSL https://github.com/lammps/lammps/archive/refs/tags/stable_2Aug2023_update3.tar.gz | tar xz && \
    cd lammps-stable_2Aug2023_update3 && \
    mkdir build && cd build && \
    cmake ../cmake \
      -DBUILD_MPI=OFF \
      -DBUILD_OMP=OFF \
      -DPKG_MOLECULE=ON \
      -DBUILD_SHARED_LIBS=ON \
      -DCMAKE_INSTALL_PREFIX=/usr/local \
      -DCMAKE_BUILD_TYPE=Release && \
    make -j2 && \
    make install && \
    ldconfig && \
    cd /tmp/lammps-stable_2Aug2023_update3/python && \
    pip install --no-cache-dir . && \
    cd / && rm -rf /tmp/lammps*

# Install Lean 4 via elan (non-interactive)
RUN curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain stable \
    && ln -s /root/.elan/bin/lean /usr/local/bin/lean \
    && ln -s /root/.elan/bin/lake /usr/local/bin/lake

# Install Docker CLI + Compose plugin (for building worker containers on-demand)
RUN DOCKER_VERSION=25.0.3 && \
    curl -fsSL "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz" | \
    tar xzf - --strip-components=1 -C /usr/local/bin docker/docker && \
    mkdir -p /usr/local/lib/docker/cli-plugins && \
    COMPOSE_VERSION=2.24.5 && \
    curl -fsSL "https://github.com/docker/compose/releases/download/v${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

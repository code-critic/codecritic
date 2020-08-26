FROM automatest/ubuntu-base

RUN apt update && DEBIAN_FRONTEND=noninteractive apt install -y \
    libpng-dev \
    libfreetype6-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    build-essential \
    xorg \
 && rm -rf /var/cache/apt/* \
 && rm -rf /var/lib/apt/lists/*

USER worker:worker

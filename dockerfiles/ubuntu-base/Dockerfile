FROM ubuntu:18.04
USER root

RUN apt update && apt install -y \
    libncurses5-dev \
    bash \
    man \
    wget \
    libpng-dev \
    libfreetype6-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    build-essential \
    xorg \
 && rm -rf /var/cache/apt/* \
 && rm -rf /var/lib/apt/lists/* \
 && adduser --system --group --disabled-password worker

COPY list-versions /bin/
COPY run.py /bin/
COPY tests/* /bin/tests/

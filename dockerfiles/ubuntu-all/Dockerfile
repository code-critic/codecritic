FROM automatest/ubuntu-base

RUN apt update && apt install -y \
    python3 \
    python3-dev \
    python3-pip \
    openjdk-8-jdk \
    gcc g++ \
    nano \
    gnupg ca-certificates \
    && apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF \
    && echo "deb https://download.mono-project.com/repo/ubuntu stable-bionic main" | tee /etc/apt/sources.list.d/mono-official-stable.list \
    && apt update \
    && apt install -y mono-devel

RUN pip3 install pytest pytest-json numpy scipy networkx matplotlib pandas seaborn

RUN rm -rf /var/cache/apt/* \
    && rm -rf /var/lib/apt/lists/*

USER worker
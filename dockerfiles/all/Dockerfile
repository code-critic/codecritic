FROM automatest/base

RUN apk update && apk add \
    python python3 \
    python-dev python3-dev \
    py-pip py3-pip \
    build-base \
    openjdk8 \
    gcc g++ \
    bash \
    gfortran \
    wget \
    freetype-dev \
    libpng-dev \
    openblas-dev \
 && ln -s /usr/include/locale.h /usr/include/xlocale.h \
 && apk add --no-cache mono --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing && \
    apk add --no-cache --virtual=.build-dependencies ca-certificates && \
    cert-sync /etc/ssl/certs/ca-certificates.crt && \
    apk del .build-dependencies


# RUN pip  install --no-cache-dir -v numpy scipy matplotlib \
#  && pip  install --no-cache-dir -v pandas seaborn


# RUN pip3 install --no-cache-dir -v numpy scipy matplotlib \
#  && pip3 install --no-cache-dir -v pandas seaborn

RUN pip3 install -v pytest \
 && pip  install -v pytest

RUN rm -rf /var/cache/apk/* \
 && rm -rf /var/lib/apt/lists/*


ENV JAVA_HOME=/usr/lib/jvm/java-1.8-openjdk \
    PATH="$JAVA_HOME/bin:${PATH}"

USER worker

ENV JAVA_HOME=/usr/lib/jvm/java-1.8-openjdk \
    PATH="$JAVA_HOME/bin:${PATH}"

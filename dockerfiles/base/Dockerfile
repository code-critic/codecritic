FROM alpine:latest
USER root

RUN apk update && apk add \
    ncurses \
    bash \
    wget \
 && rm -rf /var/cache/apk/* \
 && rm -rf /var/lib/apt/lists/* \
 && addgroup -S worker \
 && adduser -S -D worker worker

COPY list-versions /bin/
COPY run.py /bin/

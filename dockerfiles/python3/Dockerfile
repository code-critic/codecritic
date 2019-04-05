FROM automatest/base

RUN apk update && apk add \
    python3-dev py3-pip \
 && rm -rf /var/cache/apk/* \
 && rm -rf /var/lib/apt/lists/*

USER worker:worker

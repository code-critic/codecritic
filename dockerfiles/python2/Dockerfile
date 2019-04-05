FROM automatest/base

RUN apk update && apk add \
    python-dev py-pip \
 && rm -rf /var/cache/apk/* \
 && rm -rf /var/lib/apt/lists/*

USER worker:worker

FROM automatest/base

RUN apk update && apk add \
    gcc g++ \
 && rm -rf /var/cache/apk/* \
 && rm -rf /var/lib/apt/lists/*

USER worker:worker

FROM automatest/base

RUN apk update && apk add \
    openjdk8 \
 && rm -rf /var/cache/apk/* \
 && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-1.8-openjdk \
    PATH="$JAVA_HOME/bin:${PATH}"

USER worker:worker

ENV JAVA_HOME=/usr/lib/jvm/java-1.8-openjdk \
    PATH="$JAVA_HOME/bin:${PATH}"

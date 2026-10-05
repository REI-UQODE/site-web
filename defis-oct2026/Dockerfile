FROM ubuntu

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        python3-pip python3-venv python3-dev \
        default-jdk \
        golang \
        nodejs npm \
        dotnet-sdk-10.0 \
        php

COPY ./docker_init.sh /bin/init

ENTRYPOINT ["/bin/init"]
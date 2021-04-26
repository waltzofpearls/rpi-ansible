FROM resin/rpi-raspbian:stretch

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
 && rm -rf /var/lib/apt/lists/*

COPY otto /bin/otto

EXPOSE 9999
VOLUME [ "/otto" ]
WORKDIR /otto

CMD [ "/bin/otto", "--config", "/otto/otto.toml", "--log-level", "info" ]

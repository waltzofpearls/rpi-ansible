FROM resin/rpi-raspbian:stretch

RUN apt-get update && apt-get install -qq -y wget libfontconfig1 ca-certificates && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN wget https://bintray.com/fg2it/deb-rpi-1b/download_file?file_path=main%2Fg%2Fgrafana_5.1.4_armhf.deb -O grafana_5.1.4_armhf.deb && \
    dpkg -i grafana_5.1.4_armhf.deb

EXPOSE 3000

ENV GF_PATHS_HOME=/usr/share/grafana \
    GF_PATHS_CONFIG=/etc/grafana/grafana.ini \
    GF_PATHS_DATA=/var/lib/grafana \
    GF_PATHS_LOGS=/var/log/grafana \
    GF_PATHS_PLUGS=/var/lib/grafana/plugins \
    GF_PATHS_PROVISIONING=/etc/grafana/provisioning

CMD grafana-server \
        --homepath="${GF_PATHS_HOME}" \
        --config="${GF_PATHS_CONFIG}" \
        cfg:default.log.mode="console" \
        cfg:default.paths.data="${GF_PATHS_DATA}" \
        cfg:default.paths.logs="${GF_PATHS_LOGS}" \
        cfg:default.paths.plugins="${GF_PATHS_PLUGINS}" \
        cfg:default.paths.provisioning="${GF_PATHS_PROVISIONING}"

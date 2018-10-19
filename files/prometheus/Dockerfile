FROM resin/rpi-raspbian:stretch

COPY prometheus                             /bin/prometheus
COPY promtool                               /bin/promtool

EXPOSE     9090
VOLUME     [ "/prometheus" ]
WORKDIR    /prometheus
ENTRYPOINT [ "/bin/prometheus" ]
CMD        [ "--config.file=/prometheus/prometheus.yml", \
             "--storage.tsdb.path=/prometheus/data", \
             "--web.console.libraries=/prometheus/console_libraries", \
             "--web.console.templates=/prometheus/consoles" ]

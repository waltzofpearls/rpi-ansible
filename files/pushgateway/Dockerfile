FROM       resin/rpi-raspbian:stretch
EXPOSE     9091
WORKDIR    /pushgateway
ADD        pushgateway /pushgateway/bin/pushgateway
ENTRYPOINT [ "/pushgateway/bin/pushgateway" ]

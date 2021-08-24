ansible = $(shell which ansible-playbook)

all:
	@echo 'Error: make target is required.'

armv6: host ?= armv6
armv6:
	$(ansible) setup-armv6.yml --extra-vars "host=$(host)"

armv7: host ?= armv7
armv7:
	$(ansible) setup-armv7.yml --extra-vars "host=$(host)"

grafana:
	$(ansible) setup-grafana.yml

healthstats:
	@env $(shell cat .healthstats.env | xargs) $(ansible) setup-healthstats.yml

prometheus:
	$(ansible) setup-prometheus.yml

sensehat:
	$(ansible) setup-sensehat.yml

otto:
	@env $(shell cat .otto.env | xargs) $(ansible) setup-otto.yml

reckon:
	$(ansible) setup-reckon.yml

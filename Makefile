ansible = $(shell which ansible-playbook)

all:
	@echo 'Error: make target is required.'

init:
	$(ansible) setup-init.yml

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

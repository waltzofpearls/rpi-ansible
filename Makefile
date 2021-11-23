ansible = $(shell which ansible-playbook)

.PHONY: all
all:
	@echo 'Error: make target is required.'

.PHONY: armv6
armv6: host ?= armv6
armv6:
	$(ansible) setup-armv6.yml --extra-vars "host=$(host)"

.PHONY: armv7
armv7: host ?= armv7
armv7:
	$(ansible) setup-armv7.yml --extra-vars "host=$(host)"

.PHONY: grafana
grafana:
	$(ansible) setup-grafana.yml

.PHONY: healthstats
healthstats:
	@env $(shell cat .healthstats.env | xargs) $(ansible) setup-healthstats.yml

.PHONY: prometheus
prometheus:
	$(ansible) setup-prometheus.yml

.PHONY: sensehat
sensehat:
	$(ansible) setup-sensehat.yml

.PHONY: otto
otto:
	@env $(shell cat .otto.env | xargs) $(ansible) setup-otto.yml

.PHONY: reckon
reckon: cert
	$(ansible) setup-reckon.yml

cert:
	# create CA
	certstrap --depot-path cert init --common-name "gRPC Root CA"
	# create server cert request
	certstrap --depot-path cert request-cert --domain localhost
	# create client cert request
	certstrap --depot-path cert request-cert --cn grpc_client
	# sign server and client cert requests
	certstrap --depot-path cert sign --CA "gRPC Root CA" localhost
	certstrap --depot-path cert sign --CA "gRPC Root CA" grpc_client
	@tree -hrC cert

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
	@env `cat .healthstats.env` $(ansible) setup-healthstats.yml

.PHONY: prometheus
prometheus:
	$(ansible) setup-prometheus.yml

.PHONY: sensehat
sensehat:
	$(ansible) setup-sensehat.yml

.PHONY: otto
otto:
	@env `cat .otto.env` $(ansible) setup-otto.yml

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

.PHONY: k3s
k3s:
	@env `cat .k3s.env` $(ansible) setup-k3s.yml

k3s-everything: | update-submodule install-k3s
	mkdir -p ~/.kube
	scp pi@k3s-one.rpi.topbass.studio:~/.kube/config ~/.kube/config
	make k3s

update-submodule:
	git submodule update --recursive

install-k3s:
	$(ansible) k3s/site.yml -i k3s/inventory/gondor/hosts.ini

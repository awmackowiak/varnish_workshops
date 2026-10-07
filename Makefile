COMPOSE ?= podman-compose
PODMAN ?= podman
.PHONY: up down check reload vsh reset solution
up:
	$(COMPOSE) up -d --build
down:
	$(COMPOSE) down
check:  ## fails unless Varnish is exactly 6.0.18
	$(COMPOSE) exec varnish varnishd -V 2>&1 | grep "varnish-6.0.18"
reload: ## load edited VCL without restart
	$(COMPOSE) exec varnish bash -c 'n=v$$(date +%s)_$$RANDOM; varnishadm vcl.load $$n /etc/varnish/default.vcl && varnishadm vcl.use $$n'
vsh:
	$(COMPOSE) exec varnish bash
reset:  ## restore the starter VCL
	cp solutions/01-request-flow.vcl varnish/vcl/default.vcl
	$(MAKE) reload
solution: ## mentor: load a solution, e.g. make solution N=02-ttl
	cp solutions/$(N).vcl varnish/vcl/default.vcl
	$(MAKE) reload

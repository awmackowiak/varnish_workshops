COMPOSE ?= podman-compose
PODMAN ?= podman
PYTHON ?= python3
MARP_VERSION := 4.5.1
.PHONY: up down check reload vsh reset solution test test-lab slides
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
	cp solutions/00-starter.vcl varnish/vcl/default.vcl
	$(MAKE) reload
test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v
test-lab: check
	COMPOSE="$(COMPOSE)" $(PYTHON) tests/rehearse.py
slides:
	npx --yes @marp-team/marp-cli@$(MARP_VERSION) slides.md --html -o slides.html
solution: ## mentor: load a solution, e.g. make solution N=04-ttl-vary
	cp solutions/$(N).vcl varnish/vcl/default.vcl
	$(MAKE) reload

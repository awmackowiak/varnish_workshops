#!/bin/sh
# Runs varnishd in foreground; VCL is mounted at /etc/varnish/default.vcl
# varnishadm inside the container connects via the local working dir (no -T needed).
exec varnishd -F -f /etc/varnish/default.vcl -a :6081 \
  -s malloc,${VARNISH_MEM:-128m} ${VARNISH_EXTRA_ARGS}

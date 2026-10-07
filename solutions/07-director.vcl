vcl 4.0;

import directors;

probe healthz {
    .url = "/healthz";
    .interval = 2s;
    .timeout = 1s;
    .window = 3;
    .threshold = 2;
}

backend backend1 {
    .host = "backend1";
    .port = "8080";
    .probe = healthz;
}

backend backend2 {
    .host = "backend2";
    .port = "8080";
    .probe = healthz;
}

sub vcl_init {
    new pool = directors.round_robin();
    pool.add_backend(backend1);
    pool.add_backend(backend2);
}

# Lab only: do not copy broad private-network authorization to production.
acl purge {
    "localhost";
    "127.0.0.1";
    "10.0.0.0"/8;
    "172.16.0.0"/12;
    "192.168.0.0"/16;
}

sub vcl_recv {
    set req.http.X-Workshop = "varnish-lab";
    unset req.http.X-Remove-Me;
    set req.backend_hint = pool.backend();
    if (req.url ~ "^/static([?].*)?$") {
        unset req.http.Cookie;
    }
    if (req.http.Host == "example.com" && req.url ~ "^/test1([?].*)?$") {
        set req.backend_hint = backend1;
        set req.url = regsub(req.url, "^/test1", "/nocache");
    }
    if (req.method == "PURGE") {
        if (!client.ip ~ purge) {
            return (synth(403, "Not allowed"));
        }
        return (purge);
    }
}

sub vcl_backend_response {
    if (bereq.is_bgfetch && beresp.status >= 500) {
        return (abandon);
    }
    if (beresp.status >= 500) {
        set beresp.uncacheable = true;
        set beresp.ttl = 0s;
        return (deliver);
    }
    if (bereq.url ~ "^/time([?].*)?$") {
        set beresp.ttl = 5s;
        set beresp.grace = 1m;
        set beresp.keep = 30s;
    }
    # Public mock endpoint only; never remove real session headers globally.
    if (bereq.url ~ "^/cookie([?].*)?$") {
        unset beresp.http.Set-Cookie;
    }
}

sub vcl_deliver {
    unset resp.http.Server;
    set resp.http.X-Workshop = "varnish-lab";
    set resp.http.X-Cache-Hits = obj.hits;
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
}

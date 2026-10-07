vcl 4.0;

backend backend1 {
    .host = "backend1";
    .port = "8080";
}

# Lab only: allow host requests forwarded through the container network.
# Production must authorize only explicitly trusted invalidation clients.
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

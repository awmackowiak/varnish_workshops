vcl 4.0;

backend backend1 {
    .host = "backend1";
    .port = "8080";
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

vcl 4.0;

backend backend1 {
    .host = "backend1";
    .port = "8080";
}

sub vcl_recv {
    set req.http.X-Workshop = "varnish-lab";
    unset req.http.X-Remove-Me;
    if (req.http.Host == "example.com" && req.url ~ "^/test1([?].*)?$") {
        set req.backend_hint = backend1;
        set req.url = regsub(req.url, "^/test1", "/nocache");
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

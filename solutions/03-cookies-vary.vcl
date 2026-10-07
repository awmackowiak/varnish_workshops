vcl 4.0;

backend default {
    .host = "backend1";
    .port = "8080";
}

sub vcl_recv {
}

sub vcl_backend_response {
    if (bereq.url ~ "^/time") {
        set beresp.ttl = 5s;
    }
    # Ex3: Set-Cookie makes objects uncacheable; strip it on /cookie
    if (bereq.url ~ "^/cookie") {
        unset beresp.http.Set-Cookie;
    }
    # /vary already works: Varnish keeps a variant per Accept-Language
}

sub vcl_deliver {
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
}

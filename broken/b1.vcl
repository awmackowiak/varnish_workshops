vcl 4.0;

import directors;

# Ex5: add the second backend AND the director in one step
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

acl purge {
    "localhost";
    "127.0.0.1";
    "10.0.0.0"/8;
    "172.16.0.0"/12;
    "192.168.0.0"/16;
}

sub vcl_recv {
    set req.backend_hint = pool.backend();
    if (req.method == "PURGE") {
        if (!client.ip ~ purge) {
            return (synth(405, "Not allowed"));
        }
        return (purge);
    }
}

sub vcl_backend_response {
    # Never cache backend errors; abandon so stale (grace) objects keep being served
    if (beresp.status >= 500) {
        return (abandon);
    }
    if (bereq.url ~ "^/time") {
        set beresp.ttl = 5s;
    }
    if (bereq.url ~ "^/cookie") {
        unset beresp.http.Set-Cookie;
    }
    if (bereq.url ~ "static") {
        set beresp.ttl = 0s;
    }
    set beresp.grace = 1m;
}

sub vcl_deliver {
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
}

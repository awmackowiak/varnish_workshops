vcl 4.0;

backend default {
    .host = "backend1";
    .port = "8080";
}

acl purge {
    "localhost";
    "127.0.0.1";
    "10.0.0.0"/8;
    "172.16.0.0"/12;
    "192.168.0.0"/16;
}

sub vcl_recv {
    set req.http.X-Forwarded-Proto = "http";
    if (req.url ~ "^/static") {
        unset req.http.Cookie;
    }
    # Ex4: PURGE restricted by ACL
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
    # Ex4: serve stale up to 1 minute while refreshing / backend is sick
    set beresp.grace = 1m;
}

sub vcl_deliver {
    unset resp.http.Server;
    set resp.http.X-Cache-Hits = obj.hits;
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
}

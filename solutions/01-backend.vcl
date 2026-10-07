vcl 4.0;

backend backend1 {
    .host = "backend1";
    .port = "8080";
}

sub vcl_deliver {
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
}

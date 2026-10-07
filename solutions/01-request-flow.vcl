vcl 4.0;

# Starter VCL: pass-through to a single backend. Exercises build on this.
backend default {
    .host = "backend1";
    .port = "8080";
}

sub vcl_recv {
}

sub vcl_backend_response {
}

sub vcl_deliver {
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
}

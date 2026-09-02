# API reference

This page is generated from [`openapi.yaml`](openapi.yaml), the machine-readable description of the
remote-interface API. That file is the source of truth: it was written by reading the two server
implementations, and everything below — including the interactive requests — comes from it.

!!! note "This page does not send requests"

    There are deliberately no **Try it out** buttons. phyphox's webserver speaks plain HTTP,
    and a browser refuses to send an `http://` request from a page it loaded over `https://`,
    so on <https://phyphox.org/docs/> every such request would be blocked before it left the
    browser. The `Access-Control-Allow-Origin: *` header the app sends does not help — the
    request never gets far enough for CORS to matter.

    Use the reference below to build the request, and send it with `curl`, a browser tab or
    your own code: enable remote access in phyphox, and use the address the app shows you.
    Every path below hangs off that address — `http://192.168.0.42:8080/get` on Android,
    where 8080 is the default port; on iOS the default is 80 and can usually be left out.
    The [introduction](index.md) covers how the requests fit together.

<swagger-ui src="openapi.yaml"/>

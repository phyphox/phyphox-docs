# API reference

This page is generated from [`openapi.yaml`](openapi.yaml), the machine-readable description of the
remote-interface API. That file is the source of truth: it was written by reading the two server
implementations, and everything below — including the interactive requests — comes from it.

!!! warning "Try it out needs this page over plain HTTP"

    The **Try it out** buttons send real requests, and phyphox's webserver speaks plain HTTP.
    A browser refuses to send an `http://` request from a page it loaded over `https://`, so on
    <https://phyphox.org/docs/> the requests are blocked before they leave the browser: the
    button spins and no response ever arrives. The `Access-Control-Allow-Origin: *` header the
    app sends does not help — the request never gets far enough for CORS to matter.

    The buttons do work when this documentation is served over HTTP, which is what
    `mkdocs serve` does when you build [the docs](https://github.com/phyphox/phyphox-docs)
    yourself. Otherwise, use the reference below to build the request and send it with `curl`,
    a browser tab or your own code — enable remote access in phyphox, and use the address the
    app shows you.

<swagger-ui src="openapi.yaml"/>

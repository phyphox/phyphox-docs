# API reference

This page is generated from [`openapi.yaml`](openapi.yaml), the machine-readable description of the
remote-interface API. That file is the source of truth: it was written by reading the two server
implementations, and everything below — including the interactive requests — comes from it.

!!! note "Try it out against your own phone"

    The **Try it out** buttons send real requests. They will not work against the phone unless the
    page is opened from a host that phyphox allows: only the Android app sends a CORS header, so a
    browser blocks these requests when the docs are served from anywhere other than the phone
    itself, and blocks them against an iPhone in every case. See
    [`cors-header`](../reference/known-inconsistencies.md).

    To use them, set the server URL below to your phone's address, which phyphox shows when you
    enable remote access.

<swagger-ui src="openapi.yaml"/>

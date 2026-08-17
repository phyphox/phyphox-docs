# Overview

[phyphox](https://phyphox.org) turns the sensors in a smartphone into physics
measuring instruments. What the app does in any given experiment is described
entirely by an experiment configuration file — so anyone can write their own
experiments, and this documentation exists to describe exactly how.

Also, phyphox features a REST API, which is documented here as well.

!!! tip "You may not need to write XML at all"

    Experiment configurations can be created visually with the
    [phyphox experiment editor](https://phyphox.org/editor), which assembles
    them from blocks in the browser and generates a QR code to get the result
    onto a phone. This site documents the underlying format, which the editor
    writes for you.

## Phyphox file format

- **[The experiment file format](file-format/index.md)** — the XML format that
  defines every phyphox experiment: data sources, analysis, views, export and metadata.
- **[Analysis modules](file-format/analysis/index.md)** — every mathematical
  operation available in the analysis stage, from `add` to Fourier transforms.
- **[Bluetooth Low Energy](file-format/bluetooth-low-energy.md)** — reading and
  writing BLE devices from an experiment.
- **[Network connections](file-format/network-connections.md)** — HTTP and MQTT
  data sources.

## Interfaces and tools

- **[The remote interface](remote-interface/index.md)** — control a running
  experiment and stream its data over HTTP.
- **[The experiment editor](https://phyphox.org/editor)** — build experiments
  visually, without writing XML by hand.
- **[Transferring experiments](transferring-experiments.md)** — getting an
  experiment onto a phone.

## Reference

- **[Version history](reference/version-history/index.md)** — what changed in each release.
- **[Known inconsistencies](reference/known-inconsistencies.md)** — where the
  implementations currently disagree with each other, and which behavior is correct.


For more information, check out [phyphox.org](phyphox.org), where you can find our forum, a wiki with some additional info and further less ressources.

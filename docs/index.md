# phyphox documentation

[phyphox](https://phyphox.org) turns the sensors in a smartphone into physics
measuring instruments. What the app does in any given experiment is described
entirely by an experiment configuration file — so anyone can write their own
experiments, and this documentation exists to describe exactly how.

## Start here

- **[The experiment file format](file-format/index.md)** — the XML format that
  defines every phyphox experiment: data sources, analysis, views, export and metadata.
- **[Analysis modules](file-format/analysis/index.md)** — every mathematical
  operation available in the analysis stage, from `add` to Fourier transforms.
- **[Bluetooth Low Energy](file-format/bluetooth-low-energy.md)** — reading and
  writing BLE devices from an experiment.
- **[Network connections](file-format/network-connections.md)** — HTTP and MQTT
  data sources.
- **[Colors](file-format/colors.md)** — the palette experiments can use.

## Interfaces and tools

- **[The remote interface](remote-interface/index.md)** — control a running
  experiment and stream its data over HTTP.
- **[The experiment editor](editor/index.md)** — build experiments visually,
  without writing XML by hand.
- **[Transferring experiments](transferring-experiments.md)** — getting an
  experiment onto a phone.

## Reference

- **[Version history](reference/version-history/index.md)** — what changed in each release.
- **[Known inconsistencies](reference/known-inconsistencies.md)** — where the
  implementations currently disagree with each other, and which behaviour is correct.

## Experiments, sensors and devices

This site documents the app itself. Material about **individual experiments, phone
sensors and Bluetooth devices** lives on the
[phyphox wiki](https://phyphox.org/wiki), where anyone can contribute and edit:

- [Built-in experiments](https://phyphox.org/wiki/index.php/Category:Built-in_experiments)
  — how each bundled experiment works and what it measures
- [User experiments](https://phyphox.org/wiki/index.php/Category:User_experiments)
  — experiments contributed by the community
- [Sensors](https://phyphox.org/wiki/index.php/Category:Sensor)
  — the phone sensors phyphox can read
- [Bluetooth device database](https://phyphox.org/wiki/index.php/Bluetooth_device_database)
  — supported BLE hardware. To build your own, see the
  [Arduino library](https://phyphox.org/arduino).

## Elsewhere

- [phyphox.org](https://phyphox.org) — the app, and experiments to download
- [Source code](https://github.com/phyphox) — all repositories
- [Sensor database](https://phyphox.org/sensordb/) — which sensors are in which phone
- [Forums](https://phyphox.org/forums/) — questions and community
- [Arduino library](https://github.com/phyphox/phyphox-arduino) ·
  [MicroPython library](https://github.com/phyphox/phyphox-micropython) ·
  [Zephyr OS library](https://github.com/vChavezB/zephyr_phyphox-ble)
  (by Victor Chávez-Bermúdez, not maintained by the phyphox team)

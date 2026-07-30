# Known inconsistencies

phyphox exists as several independent implementations: the Android app, the iOS app,
the Blockly editor, and the Arduino and MicroPython libraries. They are written
separately, by different people, at different times. Where they disagree about the
experiment file format or the remote-interface API, that disagreement is a **bug**,
not a platform difference you should design around.

This page lists the divergences we know about. Each one also raises a warning on the
documentation page it affects, so you find out where it matters rather than only here.

!!! note "This list is not complete"

    It records what has been checked so far. The absence of an entry for some
    corner of the format means nobody has compared the implementations there yet,
    not that they agree. Reconciling them is ongoing work spanning several releases.

If you hit a difference that is not listed, please
[open an issue](https://github.com/phyphox/phyphox-docs/issues) - a concrete report
with the file or request that behaves differently is genuinely useful.

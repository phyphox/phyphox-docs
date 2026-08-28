"""One session at a time on the lab bench.

The phones and the boards are shared between the sessions working in this
folder, and nothing stopped two of them driving the same hardware at once.
On 2026-08-27 that happened: a full ble pass was holding a connection to
each board (a BLE peripheral stops advertising while connected) and
issuing start over the remote API on the Pixel 3, while the Android
session was scanning for those boards from the same phone. What it saw
was a dead bench and an experiment that started measuring by itself about
a second after loading - both of them the other session, neither of them
a bug.

So a run takes a lock first. It is advisory and deliberately simple: a
file in the working root, holding who has it, on which host, since when
and with which pid. Whoever wants the bench looks there. A lock whose
process is gone is stale and taken over with a notice, because a killed
run must not park the bench for the next person.

The file is PER HOST - .bench-lock-<hostname>. The working root syncs
between the Linux machine and the MacBook, and the two benches are
different phones and different boards, so a lock from the other machine
means nothing here. The first version knew that when READING (it ignored
foreign locks) but not when WRITING: both hosts wrote one shared
.bench-lock, so whichever ran second overwrote the other's entry, and the
first run then found a lock that was not its own and stopped itself
mid-pass on the assumption that someone had taken its phones. That is
what happened on 2026-08-28 at 14:49, two scenarios into a full pass,
when the MacBook started a run of its own. One file each also means the
two machines never write the same file, which matters when the folder
between them is a sync client.
"""

import os
import socket
import time

def _host():
    return socket.gethostname()


LOCK = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
    ".bench-lock-" + _host()))


def _read():
    try:
        with open(LOCK) as f:
            fields = dict(line.split("=", 1) for line in f.read().splitlines()
                          if "=" in line)
        return {k: v.strip() for k, v in fields.items()}
    except OSError:
        return None


def _alive(pid):
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Alive and someone else's. Reading EPERM as "gone" would hand the
        # bench to a second run whenever the first belongs to another user.
        return True
    except (OSError, ValueError):
        return False
    return True


def acquire(who, force=False):
    """(ok, message). Does not block: a busy bench is a thing to report,
    not to queue behind - the other session may be mid-flash.

    The lock file is per host and still carries the host that wrote it,
    so a file that arrives from the other machine by some other route
    (a rename, a restored backup, a sync client putting one where it
    does not belong) is ignored rather than believed: a pid from the
    other machine means nothing here, and reading one as ours would
    either park this bench forever or hand it away.
    """
    held = _read()
    if held and held.get("host", _host()) != _host():
        held = None                    # not ours to honour; not ours to write
    if held and held.get("pid") and _alive(held["pid"]) and not force:
        return False, (f"the bench is held by {held.get('who', '?')} "
                       f"(pid {held['pid']}, since {held.get('since', '?')}). "
                       f"Wait for it, or pass --force-bench if you are sure "
                       f"that run is gone - two sessions on one bench cost "
                       f"an afternoon once already")
    note = ""
    if held and held.get("pid") and not _alive(held["pid"]):
        note = (f" (took over a stale lock from {held.get('who', '?')}, "
                f"pid {held['pid']})")
    with open(LOCK, "w") as f:
        f.write(f"who={who}\nhost={_host()}\npid={os.getpid()}\n"
                f"since={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    return True, "bench locked" + note


def owns():
    """Is the lock still ours?

    Worth asking again mid-run, not just at the start. A run that loses
    the bench does not fail cleanly - it produces measurements of a phone
    somebody else is resetting, which look exactly like an intermittent
    app bug and cost an afternoon to disbelieve. Better to stop and say
    so.
    """
    held = _read()
    return bool(held and held.get("pid") == str(os.getpid())
                and held.get("host", _host()) == _host())


def release():
    held = _read()
    if (held and held.get("pid") == str(os.getpid())
            and held.get("host", _host()) == _host()):
        try:
            os.remove(LOCK)
        except OSError:
            pass

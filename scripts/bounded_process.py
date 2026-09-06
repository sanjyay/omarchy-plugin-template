"""Optional POSIX one-shot process supervisor. No import-time signal handlers."""
from dataclasses import dataclass
import math
import os
import selectors
import signal
import subprocess
import time


@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: bytes
    stderr: bytes
    reason: str  # exited, timeout, cancelled, stdout-limit, stderr-limit


def run(argv, *, timeout=10.0, stdout_limit=65536, stderr_limit=16384,
        cancelled=lambda: False, cwd=None, env=None):
    """Run trusted argv without a shell; stdin is closed, both pipes are bounded.

    Caller owns executable selection, environment policy and cancellation.
    Descendants must remain in the new process group (no daemonization).
    SIGKILL is sent to that group on every exit, before reaping its leader.
    Intended for Linux. It is resource control, not a security sandbox.
    """
    if (not isinstance(argv, (list, tuple)) or not argv
            or any(not isinstance(s, str) or '\0' in s for s in argv)
            or not argv[0]):
        raise ValueError('argv must be a nonempty list of NUL-free strings')
    if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout must be finite and positive')
    for limit in (stdout_limit, stderr_limit):
        if type(limit) is not int or not 0 <= limit <= 16 * 1024 * 1024:
            raise ValueError('stream limits must be integers between 0 and 16 MiB')
    if cancelled():
        return Result(-signal.SIGKILL, b'', b'', 'cancelled')
    deadline = time.monotonic() + timeout
    output = {'stdout': bytearray(), 'stderr': bytearray()}
    limits = {'stdout': stdout_limit, 'stderr': stderr_limit}
    reason = 'exited'
    proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True,
                            cwd=cwd, env=env)
    try:
        with selectors.DefaultSelector() as selector:
            for name, pipe in [('stdout', proc.stdout), ('stderr', proc.stderr)]:
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)
            while True:
                if cancelled():
                    reason = 'cancelled'
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    reason = 'timeout'
                    break
                # WNOWAIT keeps the leader PID reserved until group cleanup.
                exited = os.waitid(os.P_PID, proc.pid,
                                   os.WEXITED | os.WNOHANG | os.WNOWAIT)
                if exited is not None and not selector.get_map():
                    break
                if not selector.get_map():
                    time.sleep(min(0.02, remaining))
                    continue
                for key, _ in selector.select(min(0.05, remaining)):
                    name = key.data
                    try:
                        chunk = os.read(key.fd, 65536)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    room = limits[name] - len(output[name])
                    output[name].extend(chunk[:room])
                    if len(chunk) > room:
                        reason = name + '-limit'
                        break
                if reason != 'exited':
                    break
    finally:
        # No poll()/wait() before this: even an exited leader anchors the PGID.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        finally:
            proc.stdout.close()
            proc.stderr.close()
            proc.wait()
    return Result(proc.returncode, bytes(output['stdout']), bytes(output['stderr']), reason)

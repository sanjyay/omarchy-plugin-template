# Optional runtime scripts

The starter has no runtime scripts to launch. bounded_process.py is a removable
library for finite Python helper operations. See [its contract](../ARCHITECTURE.md).
Keep it only if needed; remove tests/test_process.py along with it. tools/check
also works without it, inheriting external tool output instead of collecting it.

Example inside a Python helper in this directory:

```python
import signal
from bounded_process import run

cancelled = False

def request_stop(signum, frame):
    global cancelled
    cancelled = True

signal.signal(signal.SIGTERM, request_stop)
signal.signal(signal.SIGINT, request_stop)
result = run(["/usr/bin/hyprctl", "-j", "monitors"], timeout=3,
             stdout_limit=65536, stderr_limit=4096,
             cancelled=lambda: cancelled)
# Accept only reason == "exited" and returncode == 0, then validate JSON schema.
```

No command runs on import. This example is guidance, not a bundled executable.
Choose environment variables deliberately for each integration. Do not expose
an arbitrary command execution endpoint to user settings. Call the helper from
QML with a structured Process command, and assign cancellation/lifecycle ownership
in a service. Secrets belong neither in argv nor logs. Bound the final protocol
response as well as child output.

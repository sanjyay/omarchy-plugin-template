# Starter architecture

The host loads `entryPoints.barWidget` from [manifest.json](manifest.json), which
maps to [Main.qml](Main.qml). The filename is a template choice; the mapping is
Omarchy's contract. This is a passive label widget using `qs.Ui.BarWidget` and
host typography. It has no daemon, persistent state, network traffic or external
installation artifacts. There is deliberately no keepLoaded flag.

The installed host injects `bar`, `moduleName` and `settings`. Main.qml validates
its optional label input, owns derived presentation state and renders plain text.
The host owns placement, settings persistence and instance destruction. A bar
instance can exist on each monitor even with allowMultiple false: that flag
prevents duplicate layout entries, not multiple screen instances.

## Grow only where needed

| Location | Responsibility | When to add |
|---|---|---|
| Main.qml | Entry contract, composition, small local interaction | Always |
| services/Service.qml | One owner for state, requests, errors and cancellation | Shared or view-independent work |
| components/ | Presentation with explicit properties and request signals | Repeated UI or a complex independent view |
| Model.js | Pure parsing, validation or geometry | Enough logic to benefit from isolated tests |
| scripts/ | OS/process/filesystem work behind a small validated protocol | APIs cannot supply the feature |
| tools/ | Development commands, never launched by the plugin | Already included |
| tests/ | Temporary fixtures and behavioral tests | Extend with each feature |

The optional directories are not pre-created. A two-file plugin should remain
understandable without services or components. A shared service requires adding
`service` to kinds and mapping `entryPoints.service`; inspect the installed
registry's injection/service lookup contract first. A nested popup does not need
an additional panel kind unless independently exposed to the host. Changing kind
requires changing the QML root/injections as well as the manifest.

## Optional subprocess helper

`scripts/bounded_process.py` is independently written
infrastructure motivated by Scope, Cursor Theme Manager, RSS and Tempo. Delete
it and its dedicated test file if unused. No runtime starter code imports it.
The development checker uses it when available and otherwise inherits validator
output without collecting it.

`run([absolute_executable, argument], timeout=5, stdout_limit=65536,
stderr_limit=16384, cancelled=event.is_set)` returns bytes, returncode and reason.
It closes stdin, drains both pipes with selectors, uses a monotonic deadline and
starts a new session. It preserves the unreaped leader until group cleanup to
avoid targeting a reused group ID. It kills remaining group members on success,
failure, timeout, cancellation and exceptions; direct-child exit alone is not
proof of cleanup. Output is truncated only with an explicit limit failure.

This small helper intentionally uses immediate SIGKILL at cleanup: it is for
finite queries and expendable calculations, not commands that must flush a
transaction or restore desktop state. Such work needs an operation-specific
cooperative stop/TERM protocol before forced termination. It does not supervise
children that escape the group, survive the helper being killed, or remain in
uninterruptible kernel sleep. Use a cgroup/user service for those requirements.
The OS spawn/reap itself cannot be given an absolute userspace wall-clock bound.

Caller policy remains explicit: executable selection, environment, input/output
schema, redaction and concurrency. Importing the helper has no signal side effects.
A QML-facing Python script should install its own lightweight SIGTERM/SIGINT
handlers that set a cancellation flag and pass that flag into run. Its bounded
JSON response needs its own encoded-size budget; JSON escaping can expand bytes.
Keep all operations off the UI thread. A generation token in the service prevents
late responses from replacing newer state. There is no generic QML runner because
stream completion, result schemas and persistence semantics differ by operation.

## Integration and ownership

Use existing host services before creating another provider. Keep compositor
queries/actions in the state owner; components should emit intent. Monitor-local
geometry belongs to the view/controller for that screen. Never start a second
Quickshell shell for a plugin.

No installer or uninstaller is needed for this starter. Omarchy clones and
validates the repository and removes/unloads it through its plugin commands;
arbitrary install hooks are not a runtime dependency mechanism. If integrations
are introduced, separately design exact artifact ownership, baseline persistence,
upgrade compatibility and conservative uninstall, and test them in isolation.
Do not inherit Tempo's symlink deployment or Astra's standalone migration system.

## Tooling trust boundary

The bootstrap handles a trusted developer checkout, not attacker-controlled
runtime state. It rejects symlinks, special files and hardlinks, writes only a
fixed list, and never traverses .git. Initialization stages replacements and
keeps originals in .init-transaction. Ordinary errors roll back; power loss or
SIGKILL may leave a partial transaction. Stop concurrent edits while running it.
If interrupted, inspect .init-transaction and restore each .original to its matching
repository-relative path (including `template/README.plugin.md`) before removing that directory and retrying. Do not delete the
journal before deciding whether recovery is needed. No automatic force/reinit
mode can erase subsequent implementation work.

The public root README documents the template repository. `tools/repo_checks.py`
owns the fixed placeholder-location contract: the plugin README source is
`template/README.plugin.md`, with double-brace placeholders; existing manifest,
QML and license placeholders retain their at-sign syntax. `.template.json` records
initialization state only. The initializer renders the source into the root README
and removes the source in the same rollback transaction. Candidate validation
checks the resulting file set before any writes. An empty `template/` directory
may remain locally; unrelated files in that directory are preserved.

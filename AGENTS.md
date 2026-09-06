# Coding agent instructions

Read the affected implementation, callers and tests before editing. Inspect Git
status and preserve existing user work. Make the smallest coherent change that
fulfills the request; avoid unrelated refactors, formatting sweeps, speculative
interfaces and new dependencies without a concrete need. Do not change installed
Omarchy, desktop configuration or other repositories as part of development.

## Code and boundaries

- Use four spaces in QML/Python, two in JSON/YAML; use explicit names and small
  functions. Match nearby conventions when extending existing code.
- Keep Main.qml as composition plus small view-local behavior. Extract a service
  when state outlives a view or several consumers need one authoritative owner.
  Extract components for repeated UI or independently testable complexity, not
  merely to reduce line counts. Pure model/geometry logic belongs in JS modules.
- Use the host's theme tokens, BarWidget settings and shared providers. Inspect
  the installed host API before using it; never guess an injection or signal.
- Prefer declarative bindings, readonly derived properties and explicit signals.
  Avoid binding loops, implicit-size feedback, and conflicting anchors/geometry.
  Mutate model state through its owner; publish changes so QML bindings observe
  them. Do not mutate host-injected settings behind the host's back.
- Render external text with Text.PlainText. Validate URLs and local resource
  paths separately; plain text does not make remote image loading safe.

## Processes and cancellation

- Prefer an existing host service or event over a command. Never block the QML
  thread. Use argument arrays; never construct shell strings from data, use
  eval, or concatenate commands into bash -c. Validate option-like arguments and
  use -- when the target program supports it. Resolve packaged paths relative
  to the component; handle file URLs with a real URL decoder.
- Every finite operation needs a monotonic deadline, independent stdout/stderr
  byte budgets, bounded inputs and bounded concurrency. A StdioCollector is
  not a byte limit. Line parsers also need protection against enormous lines.
- Use scripts/bounded_process.py for one-shot Python calls if retained. Run it
  in a helper process, never on the UI thread. Choose a trusted executable and
  an appropriate environment; this helper does not validate either for you.
- The operation owner must cancel on dismissal when appropriate, on replacement
  and on destruction. Invalidate a generation token before stopping work; ignore
  late results. Do not report partial, cancelled or timed-out output as success.
- Terminate only owned process groups; never pkill/killall by program name.
  Cleanup must include descendants even after the direct child exits. Long-lived
  monitors need a separate lifecycle protocol (parent EOF/death detection,
  bounded messages and restart backoff). Never assume killing a wrapper cleans
  its tree or that a destructor runs after a crash. Document daemon/cgroup needs.
- Signal handlers should request cancellation, not acquire locks or perform
  restoration. Do not install global signal handlers on module import.

## Filesystem and state

- Keep configuration, data, cache and runtime state in distinct plugin-specific
  XDG locations only when needed. Validate absolute environment-provided roots.
  Never write state into the installed plugin checkout or packaged Omarchy.
- Treat imported paths, archives, filenames and metadata as untrusted. Bound
  reads, counts and dimensions; reject traversal, unexpected symlinks and special
  files. Never use string-prefix tests to establish path containment.
- For security-sensitive writes, hold directory descriptors, use no-follow
  opens and verify ownership/type/identity. A realpath check followed by an open
  is vulnerable to replacement races. The bootstrap assumes a trusted checkout
  without concurrent hostile edits; do not reuse it for hostile runtime paths.
- Use private temporary directories and exclusive temporary files, with 0700
  directories and 0600 sensitive files. Stage replacements in the destination
  filesystem; preserve intended modes, handle disk-full errors, and clean only
  owned temporary artifacts. Do not use predictable shared /tmp filenames.
- Before changing user configuration, persist an original baseline and ownership
  evidence. Refuse uncertain restoration. Cleanup/migration must be idempotent,
  preserve unrelated edits and retain user data on ordinary uninstall. Never
  broaden deletion to make a failing cleanup pass. Version persistent schemas;
  test migrations from supported versions and failure halfway through.

## Lifecycle, desktop and performance

- The creator owns each timer, connection, loader, capture, process and temporary
  artifact. Release captures immediately on hide, monitor removal and teardown.
  Handle repeated open/close and partially completed startup. Avoid global
  resources per monitor; use a host-loaded service for shared jobs.
- Prefer event-driven updates. Debounce bursts, coalesce writes and suppress
  overlapping work. Poll only when the upstream API requires it; document the
  interval, bound retries and suspend idle/hidden work when semantics permit.
- Isolate Omarchy/Hyprland calls behind a narrow owner. Read compositor state
  without changing focus, geometry or fullscreen unless the feature requires it.
  Explicitly choose keyboard focus, input regions and exclusive zones for windows.
- Never assume screen zero, a fixed output name, one monitor, a horizontal bar or
  integer scale. Use the relevant screen's logical coordinates, clamp geometry,
  respect bar insets and align captures to device pixels. Test hotplug/DPMS and
  mixed scales. Decorative items must not steal input.

## Errors, verification and communication

- Distinguish empty data, missing dependency, invalid input, timeout, cancellation
  and command failure. Present a short actionable message; retain last good state
  only when clearly identified as stale. Do not swallow failures as success.
- Prefix diagnostic logs with the plugin ID and operation. Bound and sanitize
  external messages; omit credentials, environment dumps, captured content and
  personal window/feed text. Rate-limit repeated errors; debug logging is opt-in.
- Test observable behavior, not exact source spelling. Add regression coverage
  for the failure class and legitimate behavior. Use temporary HOME/XDG roots
  and fail-fast command shims for all desktop/systemd operations in tests.
  Tests must never install, reload the real shell or contact external services.
- Run ./tools/check (use --template before initialization) and ./tests/run.
  Require desktop validation before a release; report missing tools honestly.
  Inspect the diff and executable bits. Never claim visual/live validation from
  static checks. Exercise multi-monitor, focus, reload and cleanup manually when
  the feature affects them.
- Update README for behavior/configuration/dependencies and ARCHITECTURE for
  ownership changes. Keep manifest version and release claims consistent.
  Retain third-party license/provenance notices. Do not copy code across licenses
  without checking obligations. Do not commit, push or publish unless requested.

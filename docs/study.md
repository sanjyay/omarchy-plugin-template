# Source study and template decisions

Inspected 2026-09-07. [Source inventory](source-inventory.json) records repository
HEADs and non-Git file paths. Existing repositories were read-only. This is a
comparative engineering study, not certification or a complete security audit.
History means locally available commit messages/diffs; hosted PR comments were
not fetched, so no undocumented reviewer intent is inferred.

## Ecosystem contract

All ten repositories contain root manifest.json, schemaVersion 1 and explicit
kind/entry mappings. Most use root QML files; Tempo uses tempo/, and Astra uses
runtime/ with a much larger legacy/source tree. The installed
/usr/share/omarchy/bin/omarchy-plugin-validate and shell/Ui/BarWidget.qml were read
as contract references. The validator enforces the reserved omarchy.* namespace,
safe existing entry paths, kind mappings and no symlinks outside .git. Its
accepted ID syntax is broader than our deliberately lowercase, dotted init CLI.
BarWidget supplies bar/moduleName/settings, vertical/barSize and setting().

The marketplace's [publishing guide](https://omarchyplugins.com/publish.html) and
[development guide](https://omarchyplugins.com/develop.html) were checked on the
study date. A public repository, manifest, README, license and safe removal are
expected; preview.png is optional. A nested widget popup is not a separate plugin
kind. Marketplace checks do not establish security. Host contracts may evolve;
run native validation against the installation you support before publishing.

## Per-repository findings

| Repository | Structure and state/integration | Lifecycle, tests and evidence |
|---|---|---|
| astra.now-playing | One BarWidget.qml; bar-widget metadata; host omarchy.media provider; popup/player state local; no scripts or persistence helper | Visibility fix in 418e771; close synchronizes popup state; playback timer and animations need visibility/playing discipline. MIT; no AGENTS, architecture document, test suite, workflow or preview file in inventory. README install fence is unfinished. |
| mirador | Overlay WorkspaceOverview.qml; cards/previews and pure WindowModel/WindowGeometry/GestureHelper JS; CLI and optional Lua gesture snippet; event-driven compositor geometry | Capture release on dismissal/hotplug and Text.PlainText are explicit invariants. QML model/integration/security tests; AGENTS and docs/architecture/testing; MIT and preview/screenshots. README claims 2.2.0 while manifest is 2.1.1: reject version drift. No custom installer/workflow. |
| peekbar | Full bar replacement with per-screen PeekBarController, TriggerPanel and BarModel; host barConfig; transient fullscreen/hover/popup state | Debounced reveal, no focus or client fullscreen mutation; docs cover multiple edges/scales. AGENTS, architecture/requirements/testing and preview; MIT. No automated test files/CI in inventory. README still uses bare peekbar in configuration/removal while manifest is sanjyay.peekbar. No installer. |
| zen-mode | Overlay ZenMode/ZenScreen, PresentationLabel and pure Geometry.js; host settings and compositor signals; per-monitor dimming | Pure QML geometry tests plus source-based security assertions; no process facility intended; focus/input-region invariants. Some “all orientations” assertions only check source presence rather than behavior. MIT, preview, README removal; no AGENTS/architecture/CI/installer in inventory. |
| wiggle | Keep-loaded Wiggle service; native C input monitor and cursor discovery helpers; C++ animation component; private runtime cursor assets | Parent-death and stdin EOF shutdown, limited input devices, bounded untrusted cursor parsing; handoff/restore/HiDPI fixes in recent history. Python/C/C++ tests; reproducible bundled ELF CI, SECURITY and preview. MIT; no AGENTS/architecture/installer in inventory. Native binary build and input access are feature-specific. |
| scope | Overlay + launcher widget; ScopeService pipeline, components and shell helper/adapters; invocation-scoped private files and generation/cancel state | Structured argv and scoped backend groups; timeout/cancellation, protected capture/search, fail-closed masking. SECURITY, shell tests, preview, MIT; no AGENTS/architecture document or CI in inventory. AI sandbox, capture and keyring policy are feature-specific. Avoid importing wrapper PID cleanup as a complete descendant guarantee. |
| cursor-theme-manager | Service + panel; components, CursorModel JS and substantial Python integration/import/state helpers; config baseline and exact imported-file ownership | Newer security/lifecycle fixes (222dad5, 5e321a4) establish first-mutation barrier, descriptor-held state, bounded supervisor and conservative restoration. Dedicated adversarial, startup race, integration and isolation tests; nested AGENTS; preview/icons/desktop assets. GPL-3.0-or-later: no implementation copied into MIT template. No standalone install/uninstall scripts; consented integrations are managed in helpers. |
| rss-plugin | BarWidget owns fetch queue, persistence/import processes; Panel and views; pure Model.js; portal save helper; XDG data migration from old ID | Node parser, scheduling, identity, OPML and plain-text tests; bounded concurrency and explicit-read identity fixes; AGENTS, ADRs, troubleshooting, preview. MIT; no CI/install/uninstall. Unbounded collectors cannot be made safe merely by limiting results after capture. UI and operation ownership are becoming too concentrated in the entry file for a universal starter. |
| Tempo | service + bar-widget nested under tempo/; models, views, calendar providers and shell/Python helpers; XDG task store, debounced writes, optional sync systemd timers | Task/store/bridge/packaging tests and fixtures; AGENTS and provider docs; MIT plus NOTICE/dependency provenance. Install/uninstall preserve tasks and optional sync state, but custom symlink deployment and broad JSON rewriting are unsuitable defaults. Fixed timezone/location validation is plugin-specific. No root preview or workflow in inventory. |
| quickshell-astra | Full-bar runtime adapter into versions/astra and versions/default; many shared providers/modules; scripts, hooks, systemd and artifact inventory | Detailed architecture, ownership, safe-validation and migration docs; temporary-home lifecycle fixtures; exact managed binding blocks and staged source/runtime parity. AGENTS still calls it standalone while architecture describes hosted mode. MIT; no workflow in inventory. Standalone updater/provider migration machinery and stray root artifacts are not template conventions. |

## Classified recurring patterns

| Classification | Evidence | Template decision |
|---|---|---|
| GOOD REUSABLE PATTERN | Every repo's root manifest; Scope host BarWidget; Astra media host lookup | Use manifest v1 and host-owned widget configuration/services. |
| GOOD REUSABLE PATTERN | Mirador/Zen/PeekBar pure geometry/model split; Tempo/RSS pure data models | Recommend testable pure logic without creating empty model files. |
| GOOD REUSABLE PATTERN | CTM ownership/baseline tests; Astra isolated install tests | Agent rules require conservative ownership, restoration and isolated test roots. No runtime filesystem abstraction without actual data needs. |
| GOOD REUSABLE PATTERN | PeekBar per-monitor controller; Mirador event-driven previews | Explicit lifecycle/screen ownership and events before polling. |
| PLUGIN-SPECIFIC — do not include | Wiggle native monitor, Scope AI sandbox, Tempo calendar bridges, Astra full-bar migration | No binaries, systemd units, network stack, installers or universal service framework. |
| PLUGIN-SPECIFIC — do not include | PeekBar stock-bar adaptation, Mirador capture geometry | Preserve host integration principles, not full UI implementations. |
| LEGACY / UNSAFE — do not preserve | Historical standalone paths in Astra; Tempo symlink installation | A normal hosted repository, no second shell and no custom deploy path. |
| LEGACY / UNSAFE — do not preserve | Collect-all output patterns and wrapper-only cleanup | Bound streams during reading; keep group leader unreaped until cleanup. Never infer safety from a QML collector or direct-child exit. |
| LEGACY / UNSAFE — do not preserve | Imported metadata previously needed plain-text fixes in RSS; source-only test assertions in Zen/Astra | Plain text from the beginning; behavioral tooling tests and explicit limits on static assurance. |
| REPEATED PROBLEM — create a better reusable solution | IDs/URLs changed repeatedly in PeekBar/CTM/RSS/Wiggle; README/manifest drift | Fixed-target, context-escaped, preflighted initializer; no guessed repository URL. |
| REPEATED PROBLEM — create a better reusable solution | Scope and CTM process supervision; RSS/Tempo process workloads | Small optional Linux supervisor; no import-time signal registry, no shared global process state, clear cancellation contract and adversarial tests. |
| REPEATED PROBLEM — create a better reusable solution | Uneven validation/documentation across repos | One portable checker, same CI commands, root AGENTS/ARCHITECTURE with distinct purposes. |

No evidence justifies a generic logging, configuration, filesystem or migration
framework in the starter. Host settings already solve the initial configuration
need; logs and schemas should be added at real operation boundaries. Empty
services/components directories would imply architecture that is not present.

## Verification limits

The study covered manifests, inventory, entry/service code, helper boundaries,
installation/removal and available architecture/security/testing documents and
local history. Large domain implementations were inspected selectively, not
line-by-line audited. Existing test suites were not executed because their live
side effects are outside this task. Source claims in README/AGENTS were compared
to implementations and are not accepted as evidence of runtime correctness.

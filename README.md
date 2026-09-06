# @@NAME@@

@@DESCRIPTION@@

Author: @@AUTHOR@@. Plugin ID: `@@ID@@`.

This repository starts as a minimal Omarchy Quattro bar widget. Before adding
features it displays a plain-text label and follows the host's typography. It
runs inside Omarchy's existing Quickshell process. Requires the Quattro
`qs.Ui.BarWidget` contract; see [compatibility evidence](docs/study.md).

## Create your plugin

1. Use GitHub's **Use this template** on `sanjyay/omarchy-plugin-template`.
2. Clone your new repository and run:

   ```bash
   ./tools/init-plugin --name "PeekBar" --id "sanjyay.peekbar" \
     --description "Reveal the Omarchy bar in fullscreen applications" \
     --author "sanjyay"
   ```

3. Implement Main.qml, then run `./tools/check` and `./tests/run`.
4. Review the diff, commit and push to your new repository.

Python 3.10+ is required for development tooling. The starter widget itself
requires no Python. Use `./tools/init-plugin --help` for limits. Author defaults
to the first ID segment; provide it explicitly for reverse-domain IDs.
Initialization updates manifest metadata, QML ID/default label, this README,
license credit/year and .template.json. It does not rename the directory or
change Git remotes. Special characters are escaped for JSON/QML and Markdown.
Repeated initialization is refused. See [recovery](ARCHITECTURE.md) if interrupted.

The untouched template is intentionally not installable with its placeholder ID.
Run `./tools/check --template` to validate it before personalization. Initialized
projects use `./tools/check`. CI selects the mode from .template.json and tests
personalization using disposable copies.

## Implement and configure

Main.qml is a passive starting point, not a completed implementation of the
feature named in your description. Replace its label UI with your behavior.
The optional inline widget setting `label` accepts a nonempty string, capped at
80 characters; invalid values fall back to the plugin name. Place it in this
widget's layout entry in `~/.config/omarchy/shell.json`, for example:

```json
{"id": "@@ID@@", "label": "Hello"}
```

The host owns settings and placement. No user configuration is written by this
widget. On a vertical bar the label is elided to the bar's width. Add an icon or
an orientation-specific layout when your feature needs more space.

## Install, update and remove

After pushing your initialized project, install using its actual repository URL:

```bash
omarchy plugin add "$(git remote get-url origin)" --enable
```

Run that from your project's checkout. Check the remote is your new repository
before installation. Installation uses the remote commit, not uncommitted local
changes. Omarchy installs a copy; changes in a separate development checkout do
not automatically reach that copy. For live iteration edit the user-owned
installed checkout or push and update it. Do not symlink the plugin tree.

```bash
omarchy plugin update @@ID@@
omarchy plugin remove @@ID@@
```

The starter owns no files outside its checkout, so there is no custom install,
uninstall or data migration step. Document dependencies and lifecycle changes
when introducing them. Preserve user data by default on removal.

## Validate and publish

```bash
./tools/check
./tests/run
./tools/check --require-desktop
```

`tools/check` checks required files, strict JSON, metadata/kind mappings, safe
entry paths, executable scripts, Python syntax, template tokens, local Markdown
links, literal QML assets/imports, symlinks and package hygiene. It runs Bash
syntax and ShellCheck when shell scripts exist and the tools are available.
It runs installed Omarchy validation and qmllint with the shell import root;
missing optional validators are reported as SKIP. `--require-desktop` makes
missing desktop validators a failure; `--shell-imports PATH` selects another
host tree. `--portable` skips desktop validators explicitly, as hosted CI does.
Tests are separate so the checker is safe to run inside test fixtures.

These are static checks, not a security proof or a live-render test. Shell
pattern checks are conservative heuristics; dynamic paths/links and QML API
compatibility still need review. Test actual placement, theme changes, small
screens, all bar edges, mixed scales, monitor unplug/DPMS and reload on a desktop
before release. Review idle resource usage and cleanup for added features.

Keep manifest version and release documentation in agreement. Add a real optional
preview.png at repository root once there is an actual UI to show. Never ship a
fake screenshot. Publishing needs a public GitHub repository, manifest, README,
license and safe removal; check the [marketplace publishing guide](https://omarchyplugins.com/publish.html)
again before submission. The template does not publish or claim verification.

See [agent instructions](AGENTS.md), [architecture](ARCHITECTURE.md),
[study and decisions](docs/study.md) and [optional process helper](scripts/README.md).

## License

[MIT](LICENSE). Retain template copyright; initialization adds your credit.
Review license compatibility and provenance before incorporating upstream code.

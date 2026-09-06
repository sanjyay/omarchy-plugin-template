# Omarchy Plugin Template

A reusable starter for building clean, maintainable **Omarchy shell plugins**.

Instead of recreating the same repository structure, agent instructions, validation tooling, and boilerplate for every plugin, create a new repository from this template and start building.

> This is a community project and is not affiliated with or endorsed by Omarchy.

---

## Quick Start

Create a new repository from this template:

```bash
gh repo create YOUR_USERNAME/my-plugin \
  --template sanjyay/omarchy-plugin-template \
  --public \
  --clone

cd my-plugin
```

Initialize it:

```bash
./tools/init-plugin \
  --name "My Plugin" \
  --id "YOUR_USERNAME.my-plugin" \
  --description "What the plugin does"
```

Then validate the project:

```bash
./tools/check
```

That's it. Start building your plugin.

---

## Example

```bash
gh repo create sanjyay/workspace-peek \
  --template sanjyay/omarchy-plugin-template \
  --public \
  --clone

cd workspace-peek

./tools/init-plugin \
  --name "Workspace Peek" \
  --id "sanjyay.workspace-peek" \
  --description "Quickly preview workspaces in Omarchy"

./tools/check
```

The template is now an independent Git repository for your new plugin.

---

## What's Included

| Path                 | Purpose                                             |
| -------------------- | --------------------------------------------------- |
| `manifest.json`      | Omarchy plugin metadata and entry points            |
| `Main.qml`           | Minimal plugin entry point                          |
| `AGENTS.md`          | Engineering rules for Codex and other coding agents |
| `ARCHITECTURE.md`    | Architecture and ownership guidelines               |
| `tools/init-plugin`  | Personalizes the template for a new plugin          |
| `tools/check`        | Runs repository validation                          |
| `tests/`             | Tests for template tooling and reusable code        |
| `.github/workflows/` | Automated repository checks                         |

The template deliberately keeps the starting architecture small. Add services, components, scripts, or additional entry points only when the plugin actually needs them.

---

## `tools/init-plugin`

`init-plugin` turns the generic template into your plugin.

```bash
./tools/init-plugin \
  --name "Plugin Name" \
  --id "username.plugin-id" \
  --description "Plugin description"
```

For available options:

```bash
./tools/init-plugin --help
```

Initialization validates all arguments and the template before writing. It renders
`template/README.plugin.md` into the root `README.md`, replacing this repository
guide with your plugin name, ID, description and author. Use `--author` to set
the credit; it defaults to the first ID segment. The README source is removed
from the initialized plugin. Repeated initialization is rejected. Ordinary write
failures restore the original files; see `ARCHITECTURE.md` for interrupted recovery.

---

## Validation

For this uninitialized template repository, run `./tools/check --template --portable`
and `./tests/run`. CI validates the raw repository in template mode. The separate
plugin README source carries the required placeholders; this public README does not.

For an initialized plugin:

Run:

```bash
./tools/check
```

before committing or publishing changes.

You can also validate the finished plugin with Omarchy:

```bash
omarchy plugin validate .
```

---

## Using Codex

The repository includes an `AGENTS.md` designed for coding agents.

That means you can create a plugin, enter the repository, and start Codex:

```bash
codex
```

Codex automatically gets the project's engineering rules covering areas such as subprocess safety, filesystem handling, lifecycle cleanup, QML practices, testing, and scope discipline.

`ARCHITECTURE.md` contains the deeper architectural guidance. Keep implementation-specific documentation there rather than bloating this README.

---

## Repository Structure

```text
my-plugin/
├── .github/
│   └── workflows/
├── tests/
├── tools/
│   ├── check
│   └── init-plugin
├── AGENTS.md
├── ARCHITECTURE.md
├── LICENSE
├── Main.qml
├── README.md
└── manifest.json
```

The exact structure may grow with the plugin. Empty abstractions and unnecessary directories are intentionally avoided.

---

## Design Principles

* Start small and introduce abstractions only when they solve a real problem.
* Prefer event-driven integrations over unnecessary polling.
* Treat subprocesses, paths, filesystem input, and external output defensively.
* Keep plugin-specific logic out of generic infrastructure.
* Clean up resources when plugin components unload.
* Test reusable or failure-prone behavior.
* Keep `Main.qml` focused instead of turning it into the entire application.
* Run validation before shipping.

See [`AGENTS.md`](./AGENTS.md) for the full engineering rules and [`ARCHITECTURE.md`](./ARCHITECTURE.md) for architecture guidance.

---

## Faster Personal Workflow

If you create Omarchy plugins frequently, wrap the GitHub template workflow in a shell command.

For example:

```bash
new-omarchy-plugin workspace-peek
```

can create the GitHub repository, clone it into the current directory, run `tools/init-plugin`, and execute the initial checks automatically.

This reduces creating a new plugin to:

```text
idea → new repository → initialized template → build
```

---

## Updating the Template

Improvements discovered while building or reviewing real plugins should be brought back into this repository when they are generally applicable.

Examples include better validation, safer reusable patterns, improved agent instructions, CI checks, or fixes for recurring Omarchy integration problems.

Plugin-specific features should remain in their own repositories.

---

## License

MIT

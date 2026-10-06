# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.2.2] - 2026-10-06

### Changed

- One shared engine for every bar instance: a single Python backend, status
  stream and IPC target, however many screens or bars show the widget.
- The CLI capability probe is cached per binary, CLI version and catalog:
  startup drops from 88 `mullvad --help` runs to one `mullvad --version`.
- Daemon events and confirmed actions refresh only the affected reads, e.g. a
  device event runs 4 commands instead of 19.
- The 30 s status poll only runs while the live status stream is down.

### Upgrade note

- Restart DankMaterialShell once (`dms restart`) after updating from 1.2.1: the
  release adds a new file, and a running shell does not see new files on reload.

## [1.2.1] - 2026-10-06

### Fixed

- The command preview now shows the default value of required choice fields,
  such as `mullvad tunnel set daita on`.

### Changed

- Test fixtures no longer contain data from a real machine.
- New promo banner and live screenshot in the README.

## [1.2.0] - 2026-10-05

First public release.

### Added

- Full Mullvad CLI 2026.5 coverage: 88 typed forms across connection, account,
  relays, tunnel and anti-censorship, DNS and network, split tunneling, API
  access and maintenance.
- Navigation tree with per-section counts and read/change/live markers, plus a
  global search with `↑/↓` selection.
- Status card with state colors, location, relay hostname and IP, and a
  reconnect shortcut.
- Equivalent command preview on every form, with secrets masked and copy button.
- Output tabs: result, current state, full settings JSON, CLI help and live logs.
- Confirmation dialog that repeats the command and highlights destructive actions.
- `Ctrl+Enter` to run the current form.
- IPC targets `toggle`, `open` and `settings`.
- English and Brazilian Portuguese translations.

### Changed

- Plugin id is now `dankMullvadVpn` (camelCase, required by the DMS plugin
  registry). Re-enable the plugin and re-add the widget after upgrading from a
  pre-release build.

### Fixed

- The confirmation dialog no longer loses its binding after `Esc`, so later
  confirmations always open.

[1.2.2]: https://github.com/bernardopg/dms-mullvad-vpn-plugin/releases/tag/v1.2.2
[1.2.1]: https://github.com/bernardopg/dms-mullvad-vpn-plugin/releases/tag/v1.2.1
[1.2.0]: https://github.com/bernardopg/dms-mullvad-vpn-plugin/releases/tag/v1.2.0

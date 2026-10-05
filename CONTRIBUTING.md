# Contributing

Thanks for helping! Bug reports, translations and new CLI coverage are all welcome.

## Setup

Clone the repository into your plugins folder and enable it in DMS:

```sh
git clone https://github.com/bernardopg/dms-mullvad-vpn-plugin \
  ~/.config/DankMaterialShell/plugins/DankMullvadVPN
```

Set `DANK_MULLVAD_MOCK=1` in the DMS environment to work against the simulated
backend; the UI then shows **SIMULATION** and no VPN change is executed.

## Checks

```sh
scripts/check --core   # contracts and unit tests, runs anywhere
scripts/check          # also the real DMS QML smoke test (needs Wayland and Quickshell)
```

CI runs `--core`. Run the full check locally for any QML change and say so in the PR.

## Rules

- **No new runtime dependencies.** Python standard library and DMS components only.
- **Every operation and parameter is registered** in `operations.json`. Regenerate it
  with `python3 scripts/build_catalog.py` and the matrix with
  `python3 scripts/build_matrix.py`.
- **Commands run as argument arrays**, never through a shell.
- **Mutations keep their confirmation.** Credentials are never persisted, logged or
  shown unmasked.
- **Translations:** `i18n/en.json` and `i18n/pt-BR.json` must have identical keys
  and placeholders.
- **Style:** four-space indentation, `Theme` colors, small direct QML bindings.
- **Commits** follow [Conventional Commits](https://www.conventionalcommits.org/):
  `fix: handle daemon unavailable`, `feat: add relay form`.

## Testing real changes

Connection changes, account operations, resets and network settings affect a real
machine. Follow the restoration checklist in
[docs/validacao-manual.md](docs/validacao-manual.md) and state in the PR which checks
used the real CLI and which were simulated.

## Releases

Bump `version` in `plugin.json` and the engine URL in `MullvadWidget.qml`, add a
`CHANGELOG.md` section, then push a `vX.Y.Z` tag. The release workflow verifies the
version and publishes the notes.

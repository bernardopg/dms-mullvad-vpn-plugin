# Repository Guidelines

## Scope and layout

DankMullvadVPN is a Linux plugin for DankMaterialShell 1.6.2 and Quickshell,
targeting Mullvad CLI 2026.5. The root QML files implement the DankBar widget,
popout, full window, preferences, translations, and operation forms. `backend.py`
is the only runtime Python adapter. `operations.json` is the reviewed command
registry; `i18n/` contains English and Brazilian Portuguese catalogs. `docs/`
contains Portuguese architecture, coverage, security, and manual validation
instructions. Scripts and simulated CLI fixtures live in `scripts/` and `tests/`.

## Development and verification

Run `python3 -m unittest discover -s tests` for backend tests and `scripts/check`
for the complete check. The latter also requires installed Quickshell and real
DMS QML imports; set `DMS_QML_ROOT` when automatic discovery is insufficient.
`scripts/check --core` runs the portable checks without a graphical session.
Never silently treat that mode as graphical validation. Regenerate the registry
with `python3 scripts/build_catalog.py` after reviewing the help snapshot and
update `docs/matriz-cli.md` with `python3 scripts/build_matrix.py`.

## Style and safety

Use four-space indentation, descriptive names, DMS components, and `Theme`
colors. Prefer Python standard-library functions and small, direct QML bindings.
Do not introduce runtime dependencies. Register every operation and parameter;
execute argument arrays without a shell. Preserve confirmation for mutations,
command timeouts, process cleanup, credential redaction, and bounded UI logs.
Never persist accounts, vouchers, passwords, or private keys in DMS preferences.
Keep translation keys and named placeholders identical between catalogs.

## Contributions

The repository started without Git history. Conventional Commits is the adopted
convention, with subjects such as `fix: handle daemon unavailable` or `feat: add
relay form`. Pull requests must describe changed behavior, update the coverage
matrix and translations, and report the checks actually run. Identify simulated
and real read-only validation separately. Real connection changes, account
operations, resets, and network configuration tests require explicit operator
authorization and the restoration checklist. Do not publish releases, install
dependencies, or restart the user's shell as part of routine checks.

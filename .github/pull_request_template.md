## What changes

<!-- Behavior visible to users. Link the issue: Closes #123 -->

## Checks run

- [ ] `scripts/check --core`
- [ ] `scripts/check` (real DMS QML smoke test)
- [ ] Manual test against a real Mullvad daemon (read-only)
- [ ] Manual test of real changes (connection, account, network), with the restoration checklist

<!-- State which checks were simulated and which used the real CLI. -->

## Checklist

- [ ] New operations and fields are registered in `operations.json` (`scripts/build_catalog.py`)
- [ ] `docs/matriz-cli.md` regenerated (`scripts/build_matrix.py`)
- [ ] English and Portuguese translations updated with identical keys
- [ ] Mutations still require confirmation; no credentials stored or logged
- [ ] Screenshots attached for UI changes

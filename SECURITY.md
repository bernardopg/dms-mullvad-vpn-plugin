# Security Policy

This plugin drives a VPN client, so security reports get priority.

## Supported versions

Only the latest release receives fixes.

## Reporting a vulnerability

**Do not open a public issue.** Use
[GitHub private vulnerability reporting](https://github.com/bernardopg/dms-mullvad-vpn-plugin/security/advisories/new).
Include the plugin, DMS and Mullvad CLI versions, the steps to reproduce and the
impact. Expect a first reply within 7 days.

Never include real account numbers, vouchers, passwords or private keys.

## Scope

In scope: command or argument injection, credential leaks (logs, settings, UI,
exported files), bypassing a confirmation, unsafe file handling in import/export,
and orphaned processes.

Out of scope: vulnerabilities in Mullvad VPN itself (report them to
[Mullvad](https://mullvad.net/en/help/security)) or in DankMaterialShell.

## Design guarantees

- Commands run as argument arrays, never through a shell.
- Every mutation requires an explicit confirmation.
- Accounts, vouchers, passwords and private keys are never written to DMS
  settings and are redacted from output; private keys are sent over stdin.
- Exports use `0600` permissions and never overwrite files; imports refuse
  symlinks and non-object JSON.

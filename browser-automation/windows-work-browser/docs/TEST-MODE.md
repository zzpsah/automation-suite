# Windows Work Browser — Development Test Mode

`DEVOS_TEST_MODE=1` is an integration-test configuration only. It exists to exercise the product against synthetic fixtures and local services without requiring production accounts or external side effects.

## Allowed in test mode

- `localhost` / `127.0.0.1` browser fixtures
- synthetic files under a task-owned temporary workspace
- mock communication providers
- deterministic MCP capability fixtures
- generated PDF/image fixtures
- fake approval tokens created by the test harness

## Still forbidden

Test mode must not:

- expose arbitrary PowerShell, CMD, shell, AutoHotkey, or executable execution to the model
- disable artifact integrity verification
- bypass the common policy gate
- log credentials, tokens, cookies, or secret material
- send real communications without the normal approval boundary
- access production credentials or production workspaces
- silently replace failed assertions with warnings

## Promotion rule

A test-mode result can prove a component's deterministic behavior, but cannot by itself mark a production runtime gate as verified where the gate explicitly requires Windows, network, signing, external-provider, or other real-environment evidence.

Every test-mode run should label its evidence as `TEST_MODE` so it cannot be confused with production acceptance evidence.

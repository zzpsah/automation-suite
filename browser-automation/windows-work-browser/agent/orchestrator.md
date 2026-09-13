# Automation Orchestrator Contract

## Execution loop

`Observe → Understand → Plan → Validate → Act → Verify → Recover`

### Observe
Collect only the minimum browser/desktop state required for the task. Prefer structured accessibility/DOM state over screenshots when available.

### Understand
Convert the observed state and user intent into a bounded task model. Do not infer permission to perform unrelated actions.

### Plan
Produce an ordered list of `AutomationAction` objects. Every action declares capability, risk, target, arguments and reason.

### Validate
Run schema validation and the deterministic policy engine. Sensitive/destructive actions pause for human approval.

### Act
The orchestrator selects the appropriate executor:

- Playwright/CDP for browser DOM and semantic actions.
- Native Windows adapter for window manager, keyboard/mouse and native dialogs.
- Capability services for files, PDF, image, extraction and communications.

The model never invokes an executor directly.

### Verify
Every side-effecting action has a postcondition. Verification should use an independent observation where possible, for example source DOM state after a form submission rather than trusting an executor return value.

### Recover
On a recoverable failure, re-observe and generate a bounded repair action. Never silently retry destructive/sensitive actions.

## Evidence

Each action emits an audit record containing action id, timestamp, capability, policy decision, executor, result and verification evidence. Secrets and credential material must never be written to evidence logs.

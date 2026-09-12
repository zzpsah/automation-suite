# Everything Claude Code — adopted for this project

We reviewed the upstream **Everything Claude Code** approach: project rules, specialized agents, workflow commands, verification loops, testing-first development, documentation sync, and session/context discipline. The upstream project is a reusable Claude Code toolkit rather than a School Document Pipeline runtime library. urlEverything Claude Code repositoryhttps://github.com/WorldFlowAI/everything-claude-code

## What we are using

### 1. Verification loop — adopted

The upstream project emphasizes checkpoint/continuous verification. We adapted that idea into:

`global-automation/scripts/document/verify_pipeline.py`

It runs:
- Python compilation for document pipeline code
- Python compilation for GovDOC OCR
- GovDOC OCR regression tests
- GovDOC OCR smoke test
- School Document Pipeline offline smoke test

The GitHub Actions workflow now calls this single deterministic verification entrypoint.

### 2. Project rules — adopted and customized

`CLAUDE.md` and `.claude/rules/project.md` capture the actual architecture and constraints of this repository. They deliberately override generic advice where this project has stricter behavior, such as conservative metadata extraction, idempotency, B2 as primary storage, and keeping GovDOC OCR behind the adapter boundary.

### 3. Specialized review agent — adopted

`.claude/agents/pipeline-reviewer.md` provides a focused review workflow for the exact integration boundary we are working on. It checks storage/OCR separation, duplicate safety, metadata evidence, and accidental publication changes.

## What we are NOT copying

We are not copying the upstream repository wholesale. Its MCP configurations, frontend/backend skills, language-specific rules, security automation, multi-agent orchestration, and Claude-specific hooks are not automatically useful to the production School Document Pipeline.

Security/RLS changes are also intentionally outside the current integration scope.

## Why this fits the current goal

Our goal is to **test Global OCR and integrate it into the School Document Pipeline**, not to turn GovDOC OCR into an unrelated feature-development project. The adopted pieces improve the development and verification process without changing the production data architecture.

## Evidence boundary

Offline verification proves code-level behavior only. It does not prove that a production B2 object exists or that Supabase/B2 credentials work. A production run that reports `Verified B2 object is missing` must therefore be treated as a storage/data-integrity problem until the B2 object is independently verified.

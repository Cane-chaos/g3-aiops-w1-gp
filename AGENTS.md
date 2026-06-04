# ECC for Codex CLI

This repo uses the project-local Codex baseline in `.codex/config.toml`.

## Workspace Purpose

This workspace contains AIOps Week 1 learning materials and incident telemetry for the group lab. Treat `g3-data/` as raw input data unless explicitly asked to transform or commit it.

## Model Recommendations

| Task Type | Recommended Model |
|-----------|------------------|
| Routine coding, tests, formatting | GPT 5.4 |
| Complex features, architecture | GPT 5.4 |
| Debugging, refactoring | GPT 5.4 |
| Security review | GPT 5.4 |

## MCP Servers

The project baseline enables:

- GitHub
- Context7
- Exa
- Memory
- Playwright
- Sequential Thinking

Keep API keys and credentials in the user environment or user-level Codex config. Do not commit secrets.

## Multi-Agent Roles

Project-local roles are defined under `.codex/agents/`:

- `explorer` - read-only evidence gathering
- `reviewer` - correctness, security, and missing-test review
- `docs_researcher` - API and documentation verification

## Security Without Hooks

Codex does not have Claude Code hooks, so security enforcement is instruction-based:

1. Validate inputs at system boundaries.
2. Never hardcode secrets; use environment variables.
3. Review `git diff` before push.
4. Use `sandbox_mode = "workspace-write"` for normal work.
5. Prefer read-only profiles or agents for audit and review tasks.

## Lab Delivery Guidance

For the AIOps lab, prefer reproducible scripts over one-off notebook state. Expected deliverables include runnable analysis code, metric anomaly detection, log pattern analysis, `FINDINGS.md`, and `SUBMIT.md`.

# Specification: Jira Custom Connector Agent

## Objective
Create a new sample Google ADK Python agent, named `adk_custom_connector`, that demonstrates how to integrate with Jira using the `ApplicationIntegrationToolset` (Google Integration Connectors). 

## Technical Requirements
- **Directory**: `adk_custom_connector/` at the root of the repository.
- **Language/Framework**: Python, Google Agent Development Kit (ADK).
- **Tooling**: `ApplicationIntegrationToolset` pointing to:
  - Project: `vibe-cabral`
  - Location: `us-central1`
  - Connection: `jira-carlosmscabral`
- **Dependency Management**: `uv` using a `pyproject.toml` configuration (`[tool.uv] package = false`).
- **Telemetry & Deployment**:
  - Must include OpenTelemetry configuration in `pyproject.toml` and `.env.template`.
  - Must include `MODEL_LOCATION` override in `agent.py`.

## Core Guidelines & Conventions
- **Modular Structure**: Must include `app/agent.py`, `app/tools.py`, `run_agent.py`, and `__init__.py`.
- **Educational Focus**: Extensive docstrings and inline comments explaining the use of `ApplicationIntegrationToolset`.
- **Isolation**: Agent must remain strictly isolated within its own folder.
- **Environment**: Ensure `.env.template` is provided containing `MODEL_LOCATION=global` and all mandatory OTEL env vars.

## Acceptance Criteria
- Code successfully validates under `uv run`.
- Agent responds via `adk run` or `adk web`.
- Integrates seamlessly with the specified Integration Connector connection (`jira-carlosmscabral`).

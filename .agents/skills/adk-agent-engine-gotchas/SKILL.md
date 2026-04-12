---
name: adk-agent-engine-gotchas
description: >
  MUST READ when deploying ADK agents to Agent Engine and encountering errors —
  model 404s, 401s from tools or Gemini Enterprise, token expiration in long
  sessions, or env var conflicts. Covers verified fixes with ADK source analysis.
metadata:
  license: Apache-2.0
  author: Carlos Cabral
  version: "2.0"
---

# Agent Engine Deployment Gotchas

Field-tested fixes for common ADK Agent Engine deployment failures.
Each issue includes root-cause analysis against ADK v1.28.0 source code.

## When This Skill Applies

**Activate when ANY of these are true:**

- Deploying an ADK agent to Agent Engine (especially with preview models or cross-project tools)
- **404 / ModelNotFoundError** after deployment
- **401 Unauthorized** from tool calls (DataAgentToolset, etc.)
- Agent works locally but fails on Agent Engine
- Agent works in Agent Engine Playground but fails from Gemini Enterprise
- Agent works initially but fails after ~1 hour of inactivity
- Questions about `GOOGLE_CLOUD_LOCATION` or env var conflicts on Agent Engine

---

# Gotcha 1: Preview Model Location Conflict (404)

## Problem

Preview models (`gemini-3-flash-preview`, `gemini-3-pro-preview`) require
`location=global`, but Agent Engine sets `GOOGLE_CLOUD_LOCATION` to the
deployment region (e.g. `us-central1`). The ADK `Gemini` class creates
`google.genai.Client()` without an explicit `location` — it reads the env
var, gets the wrong region, and the model returns 404.

**Key insight**: Session services use a **separate** env var
(`GOOGLE_CLOUD_AGENT_ENGINE_LOCATION`), NOT `GOOGLE_CLOUD_LOCATION`. These
are decoupled in the ADK source. The model location can be overridden safely.

## Fix: GlobalGemini Subclass

Override `api_client` to pass `location="global"` explicitly:

```python
import os
from functools import cached_property
from google.adk.models import Gemini
from google.genai import Client, types

class GlobalGemini(Gemini):
    """Forces location='global' for the LLM client, decoupled from
    Agent Engine's regional GOOGLE_CLOUD_LOCATION."""

    @cached_property
    def api_client(self) -> Client:
        return Client(
            http_options=types.HttpOptions(
                headers=self._tracking_headers(),
                retry_options=self.retry_options,
                base_url=self.base_url,
            ),
            location="global",
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        )
```

Usage: `model=GlobalGemini(model="gemini-3-flash-preview")`

See `references/global-gemini.md` for full details, source evidence, and
migration guide.

## Anti-Patterns to AVOID

**Never override `GOOGLE_CLOUD_LOCATION` in `agent_engine_app.py`**:
```python
# BAD — affects ALL consumers (tools, telemetry, logging)
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
```
This is a shotgun fix. The subclass is a scalpel. See Gotcha 2 for what
happens when the shotgun hits unintended targets.

---

# Gotcha 2: Env Var Override Breaks Tool Endpoints (401)

## Problem

Setting `GOOGLE_CLOUD_LOCATION=global` after `set_up()` (the timing-based
approach) changes the location for ALL consumers — including tools like
`DataAgentToolset`. If a tool's API lives at a regional endpoint (not
`global`), requests go to the wrong endpoint and fail with 401.

## Observed Behavior

`data-agent-v2` worked in Agent Engine Playground but returned
**401 Unauthorized** when `DataAgentToolset` called the Data Agent API in
`cabral-apigee`. The LLM interpreted this as a permissions error.

## Root Cause

The env var override set `GOOGLE_CLOUD_LOCATION=global` for all consumers.
`DataAgentToolset` used this to construct its API endpoint. The Data Agent
service lives at a **regional** endpoint — requests to the `global` endpoint
returned 401.

## Fix

Remove ALL `GOOGLE_CLOUD_LOCATION` manipulation from `agent_engine_app.py`.
Use only the `GlobalGemini` subclass (Gotcha 1). This way:
- `GOOGLE_CLOUD_LOCATION` stays at the deployment region (tools use correct endpoints)
- Only the model client routes to `global` (via the subclass)

**Lesson**: The env var override is a shotgun — it hits every consumer.
The subclass is a scalpel — it only hits the model client.

---

# Gotcha 3: ADC Token Expiration in Long-Lived Sessions (401)

## Problem

Agent works on first use but returns **401 after ~1 hour** of inactivity.
Applies to any agent using ADC credentials with tools that extract
`credentials.token` (e.g. `DataAgentToolset`).

## Root Cause

ADC on Agent Engine returns `google.auth.compute_engine.Credentials` (NOT
`google.oauth2.credentials.Credentials`). The ADK's credential manager
at `_google_credentials.py:193` shortcuts non-OAuth2 credentials:

```python
if creds and not isinstance(creds, google.oauth2.credentials.Credentials):
    return creds  # ← NO REFRESH CHECK, returned immediately
```

Then `_get_http_headers()` reads `credentials.token` — a cached string from
the initial refresh at module load time. After the ~1-hour token TTL, all
tool API calls fail with 401.

## Fix: AutoRefreshCredentials Wrapper

```python
class AutoRefreshCredentials(google.auth.credentials.Credentials):
    """Wraps ADC to auto-refresh the token before it's read."""

    def __init__(self, base_credentials):
        self._base = base_credentials
        # Skip super().__init__() — it sets self.token = None

    @property
    def token(self):
        if not self._base.valid:
            self._base.refresh(google.auth.transport.requests.Request())
        return self._base.token

    @token.setter
    def token(self, value):
        pass  # managed by _base

    @property
    def valid(self):
        return self._base.valid

    @property
    def expired(self):
        return self._base.expired

    @property
    def expiry(self):
        return self._base.expiry

    @expiry.setter
    def expiry(self, value):
        pass  # managed by _base

    def refresh(self, request):
        self._base.refresh(request)
```

Usage:
```python
application_default_credentials, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
credentials_config = DataAgentCredentialsConfig(
    credentials=AutoRefreshCredentials(application_default_credentials)
)
```

**Notes**:
- Must inherit from `google.auth.credentials.Credentials` (Pydantic
  validation in `DataAgentCredentialsConfig` checks `isinstance`)
- Must provide no-op setters for `token` and `expiry` (base `__init__`
  tries to set them — we skip calling it but the setters prevent errors
  if anyone else calls them)

---

# Clean agent_engine_app.py Template

When using the fixes above, `agent_engine_app.py` should be minimal —
NO env var manipulation:

```python
import logging
import vertexai
from dotenv import load_dotenv
from vertexai.agent_engines.templates.adk import AdkApp
from app.agent import app as adk_app

load_dotenv()

class AgentEngineApp(AdkApp):
    def set_up(self) -> None:
        vertexai.init()
        super().set_up()
        logging.basicConfig(level=logging.INFO)

agent_engine = AgentEngineApp(app=adk_app)
```

---

# Future-Proofing

These fixes become unnecessary when:
- ADK `Gemini` class adds a `location` parameter (Gotcha 1)
- ADK `GoogleCredentialsManager` refreshes non-OAuth2 credentials (Gotcha 3)
- Preview models become available at regional endpoints (Gotcha 1)

When `global` endpoint forwards to regional (as it does for GA models),
using `location="global"` is still safe — no code change needed.

---

# Reference Implementations

**Minimal (flow validation)**: `joke-agent/`
**Cross-project with tools**: `data-agent-v2/`

Both deployed to Agent Engine and registered with Gemini Enterprise (April 2026).

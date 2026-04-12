---
name: adk-global-gemini-fix
description: >
  MUST READ when deploying ADK agents with preview models (gemini-3-*-preview)
  to Agent Engine OR when encountering model 404 errors after deployment.
  Covers the location conflict between Agent Engine (regional) and preview
  models (global-only), the GlobalGemini subclass fix, and common pitfalls.
metadata:
  license: Apache-2.0
  author: Carlos Cabral
  version: "1.0"
---

# GlobalGemini Fix — Agent Engine + Preview Model Location Conflict

## When This Skill Applies

**Activate this skill when ANY of these conditions are true:**

- User is deploying an ADK agent to Agent Engine with a preview model (`gemini-3-flash-preview`, `gemini-3-pro-preview`, or any model requiring `location=global`)
- User encounters a **404 / ModelNotFoundError** after deploying to Agent Engine
- User sees errors mentioning model not available in a specific region
- User asks about `GOOGLE_CLOUD_LOCATION` conflicts with Agent Engine
- User is setting up a new ADK agent and plans to use Agent Engine + Gemini Enterprise
- Agent works locally / in playground but fails when deployed or when invoked from Gemini Enterprise

---

## The Problem

### Root Cause (Verified against ADK v1.28.0 source)

Agent Engine and preview models need **different locations**:

| Component | Required Location | How It's Set |
|-----------|------------------|--------------|
| Agent Engine session service | Regional (e.g. `us-central1`) | `GOOGLE_CLOUD_AGENT_ENGINE_LOCATION` env var |
| Preview models (gemini-3-*) | `global` | `GOOGLE_CLOUD_LOCATION` env var (read by `google.genai.Client`) |

**The conflict**: During `AdkApp.set_up()`, Agent Engine sets `GOOGLE_CLOUD_LOCATION` to the deployment region (e.g. `us-central1`). The ADK `Gemini` class creates `google.genai.Client()` **without** an explicit `location` parameter — the Client reads `GOOGLE_CLOUD_LOCATION` from the environment, gets `us-central1`, and the preview model returns 404 because it only exists at the `global` endpoint.

### Key Architectural Insight

Session services use a **separate** env var (`GOOGLE_CLOUD_AGENT_ENGINE_LOCATION`), NOT `GOOGLE_CLOUD_LOCATION`. These are decoupled in the ADK source (`adk.py` lines 810-813 vs 903-906). This means we can safely override the model's location without affecting session services.

### Source Evidence

**`google/adk/models/google_llm.py` lines 298-313** — The `Gemini.api_client` property:
```python
@cached_property
def api_client(self) -> Client:
    from google.genai import Client
    return Client(
        http_options=types.HttpOptions(
            headers=self._tracking_headers(),
            retry_options=self.retry_options,
            base_url=self.base_url,
        )
    )
```
No `location`, `vertexai`, or `project` params passed — Client falls back to env vars.

**`vertexai/agent_engines/templates/adk.py` lines 804-813** — `AdkApp.set_up()`:
```python
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
# ...
if location:
    if "GOOGLE_CLOUD_AGENT_ENGINE_LOCATION" not in os.environ:
        os.environ["GOOGLE_CLOUD_AGENT_ENGINE_LOCATION"] = location
    if "GOOGLE_CLOUD_LOCATION" not in os.environ:
        os.environ["GOOGLE_CLOUD_LOCATION"] = location
```

**`vertexai/agent_engines/templates/adk.py` lines 903-906** — Session service init:
```python
self._tmpl_attrs["session_service"] = VertexAiSessionService(
    project=project,
    location=agent_engine_location,  # from GOOGLE_CLOUD_AGENT_ENGINE_LOCATION
    agent_engine_id=os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID"),
)
```

---

## The Fix: GlobalGemini Subclass

### Recommended Approach

Subclass `Gemini` and override `api_client` to pass `location="global"` explicitly:

```python
import os
from functools import cached_property

from google.adk.models import Gemini
from google.genai import Client, types


class GlobalGemini(Gemini):
    """Gemini subclass that forces location='global' for the LLM client.

    Agent Engine sets GOOGLE_CLOUD_LOCATION to its deployment region (e.g.
    us-central1) for session services, but preview models like
    gemini-3-flash-preview are only available at the 'global' endpoint.
    This subclass decouples the model endpoint from the session endpoint
    by explicitly passing location='global' to the google.genai.Client.
    """

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

### Usage in Agent Definition

```python
root_agent = Agent(
    name="root_agent",
    model=GlobalGemini(
        model="gemini-3-flash-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="...",
)
```

### Why This Works

1. `api_client` is a `@cached_property` — created once, lazily, on first model call (well after `set_up()` completes)
2. Explicitly passes `location="global"` — bypasses `GOOGLE_CLOUD_LOCATION` env var entirely
3. Session services use `GOOGLE_CLOUD_AGENT_ENGINE_LOCATION` — unaffected by this override
4. `_tracking_headers()` is a stable inherited method calling public `get_tracking_headers()` from `google.adk.utils`
5. `vertexai=True` + `project` are required when explicitly setting location on `google.genai.Client`

---

## Approaches to AVOID

### DO NOT: Env var timing override in agent_engine_app.py

```python
# BAD — fragile timing dependency
class AgentEngineApp(AdkApp):
    def set_up(self):
        super().set_up()  # sets GOOGLE_CLOUD_LOCATION=us-central1
        os.environ["GOOGLE_CLOUD_LOCATION"] = "global"  # override after
```

**Why it's bad:**
- Depends on init ordering — if ADK changes when services read the env var, it breaks silently
- Side effects: telemetry, logging, and other consumers also read `GOOGLE_CLOUD_LOCATION`
- Redundant with the subclass fix — if using GlobalGemini, this is unnecessary

### DO NOT: Set GOOGLE_CLOUD_LOCATION=global at module level in agent.py

```python
# BAD — can be overridden by AdkApp.set_up()
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
```

**Why it's bad:**
- `AdkApp.set_up()` checks `if "GOOGLE_CLOUD_LOCATION" not in os.environ` — it WON'T override if pre-set
- BUT this means `GOOGLE_CLOUD_LOCATION` stays "global" for everything, including telemetry
- Doesn't address the root cause (model client needs its own location)

### DO NOT: Use both fixes simultaneously

The data-agent-v2 originally used both the subclass AND the env var override. This is redundant — the subclass alone is sufficient. The double-fix adds complexity and confusion.

---

## agent_engine_app.py — Keep It Clean

When using the GlobalGemini subclass, `agent_engine_app.py` should be minimal:

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

No `GOOGLE_CLOUD_LOCATION` manipulation. No `gemini_location` capture. The GlobalGemini subclass handles everything.

---

## Detecting When This Fix Is Needed

### Symptoms

1. **404 ModelNotFoundError** after deploying to Agent Engine
2. Agent works locally (`adk web .`) but fails on Agent Engine
3. Agent works in Agent Engine Playground but fails when **Gemini Enterprise** invokes it
4. Error messages mentioning model not found in `us-central1` (or other regional endpoint)

### Trigger Conditions

Apply the GlobalGemini fix when ALL of these are true:
- Using a model that requires `global` location (currently: `gemini-3-flash-preview`, `gemini-3-pro-preview`)
- Deploying to Agent Engine (which forces regional `GOOGLE_CLOUD_LOCATION`)
- The ADK `Gemini` class does not yet support a `location` parameter (check: if `Gemini.__init__` accepts `location`, the fix is no longer needed)

### Future-Proofing

This fix will become unnecessary when either:
- The ADK `Gemini` class adds a `location` parameter
- Preview models become available at regional endpoints
- Agent Engine stops overriding `GOOGLE_CLOUD_LOCATION`

When the `global` endpoint forwards to regional (which it does for GA models), using `location="global"` is still safe — no code change needed.

---

## Gemini Enterprise Session Considerations

When an agent is invoked via **Gemini Enterprise** (not the Agent Engine Playground), the session flow is different:

- Gemini Enterprise creates its own session context
- The Agent Engine's `VertexAiSessionService` handles session persistence
- Session services use `GOOGLE_CLOUD_AGENT_ENGINE_LOCATION` (separate from `GOOGLE_CLOUD_LOCATION`)

If an agent works in Playground but fails from Gemini Enterprise, check:
1. The `agent_engine_app.py` is NOT manipulating `GOOGLE_CLOUD_LOCATION` after `set_up()` — this can corrupt the session service's env
2. The GlobalGemini subclass is used (not env var overrides)
3. Session service initialization is clean (no env var side effects)

---

## Case Study: DataAgentToolset 401 from Env Var Override

**Problem**: `data-agent-v2` used both the GlobalGemini subclass AND an env var
timing override in `agent_engine_app.py`:
```python
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"  # after set_up()
```

The agent worked in the **Agent Engine Playground** but returned **401 Unauthorized**
when calling the `DataAgentToolset` to reach a cross-project Data Agent in
`cabral-apigee`.

**Root cause**: The env var override set `GOOGLE_CLOUD_LOCATION=global` for ALL
consumers — including `DataAgentToolset`, which uses it internally to construct
its API endpoint. The Data Agent service lives at a **regional** endpoint
(e.g. `us-central1`), not `global`. Requests to the wrong endpoint returned
401, which the LLM interpreted as a permissions error.

**Fix**: Removed the env var override from `agent_engine_app.py`. With only the
GlobalGemini subclass in place:
- `GOOGLE_CLOUD_LOCATION` stays at `us-central1` (set by `AdkApp.set_up()`)
- `DataAgentToolset` calls the correct regional endpoint
- Only the model client routes to `global` (via the subclass)

**Lesson**: The env var override is a shotgun — it affects every consumer of
`GOOGLE_CLOUD_LOCATION`. The subclass is a scalpel — it only affects the model
client. Never use both. Always prefer the subclass.

---

## Reference Implementations

**Minimal (flow validation)**:
- `joke-agent/app/agent.py` — GlobalGemini subclass + simple agent
- `joke-agent/app/agent_engine_app.py` — Clean, no env var hacks

**Cross-project with tools**:
- `data-agent-v2/app/agent.py` — GlobalGemini + DataAgentToolset (cross-project)
- `data-agent-v2/app/agent_engine_app.py` — Clean, no env var manipulation

Both deployed to Agent Engine and registered with Gemini Enterprise (April 2026).

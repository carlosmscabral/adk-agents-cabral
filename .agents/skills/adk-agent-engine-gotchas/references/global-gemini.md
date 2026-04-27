# GlobalGemini Fix — Full Details

## Source Evidence (ADK v1.28.0)

**`google/adk/models/google_llm.py` lines 298-313** — `Gemini.api_client`:
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
No `location`, `vertexai`, or `project` params — Client reads env vars.

**`vertexai/agent_engines/templates/adk.py` lines 804-813** — `AdkApp.set_up()`:
```python
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
if location:
    if "GOOGLE_CLOUD_AGENT_ENGINE_LOCATION" not in os.environ:
        os.environ["GOOGLE_CLOUD_AGENT_ENGINE_LOCATION"] = location
    if "GOOGLE_CLOUD_LOCATION" not in os.environ:
        os.environ["GOOGLE_CLOUD_LOCATION"] = location
```

**`vertexai/agent_engines/templates/adk.py` lines 903-906** — Session service:
```python
self._tmpl_attrs["session_service"] = VertexAiSessionService(
    project=project,
    location=agent_engine_location,  # from GOOGLE_CLOUD_AGENT_ENGINE_LOCATION
    agent_engine_id=os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID"),
)
```

## Why the Subclass Works

1. `api_client` is `@cached_property` — created lazily after `set_up()`
2. Passes `location="global"` explicitly — bypasses env var
3. Session services use `GOOGLE_CLOUD_AGENT_ENGINE_LOCATION` — unaffected
4. `_tracking_headers()` is stable (calls public `get_tracking_headers()`)
5. `vertexai=True` + `project` required when setting location on `genai.Client`

## How to Apply

### 1. Add GlobalGemini to agent.py

```python
import os
from functools import cached_property
from google.adk.models import Gemini
from google.genai import Client, types

class GlobalGemini(Gemini):
    """Forces location='global' for the LLM client."""

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

### 2. Use in Agent constructor

```python
# BEFORE (broken on Agent Engine)
model=Gemini(model="gemini-3-flash-preview")

# AFTER (works on Agent Engine)
model=GlobalGemini(model="gemini-3-flash-preview")
```

### 3. Clean up agent_engine_app.py

Remove ALL `GOOGLE_CLOUD_LOCATION` manipulation.

### 4. Clean up agent.py env vars

```python
# REMOVE:
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

# KEEP:
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
```

### 5. Multi-agent systems

Apply GlobalGemini only to agents using preview models:
```python
sub_agent = Agent(model=Gemini(model="gemini-2.5-flash"), ...)         # GA — no fix
root_agent = Agent(model=GlobalGemini(model="gemini-3-flash-preview"), ...)  # preview — needs fix
```

### 6. Verify

```bash
make playground   # local test
make deploy       # deploy
# Test from Playground AND Gemini Enterprise
```

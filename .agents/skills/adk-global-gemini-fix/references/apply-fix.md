# How to Apply the GlobalGemini Fix

## Step-by-Step Checklist

### 1. Add GlobalGemini to agent.py

Add this class BEFORE the agent definition. The class can be placed at the
module level alongside other imports:

```python
import os
from functools import cached_property

from google.adk.models import Gemini
from google.genai import Client, types


class GlobalGemini(Gemini):
    """Gemini subclass that forces location='global' for the LLM client."""

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

### 2. Use GlobalGemini in the Agent constructor

Replace `Gemini(model="gemini-3-flash-preview")` with
`GlobalGemini(model="gemini-3-flash-preview")`:

```python
# BEFORE (broken on Agent Engine)
root_agent = Agent(
    model=Gemini(model="gemini-3-flash-preview"),
    ...
)

# AFTER (works on Agent Engine)
root_agent = Agent(
    model=GlobalGemini(model="gemini-3-flash-preview"),
    ...
)
```

### 3. Clean up agent_engine_app.py

Remove any `GOOGLE_CLOUD_LOCATION` manipulation:

```python
# REMOVE these patterns:
gemini_location = os.environ.get("GOOGLE_CLOUD_LOCATION")
# ...
if gemini_location:
    os.environ["GOOGLE_CLOUD_LOCATION"] = gemini_location

# REMOVE this pattern:
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
```

### 4. Clean up agent.py module-level env vars

Remove `GOOGLE_CLOUD_LOCATION` from module-level env var setup:

```python
# REMOVE this line:
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

# KEEP these lines:
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
```

### 5. Verify

```bash
# Local test
make playground
# Send a message, verify response (no 404)

# Deploy
make deploy
# Test via Console Playground URL

# If registered with Gemini Enterprise, test from there too
```

## Applying to Multi-Agent Systems

If your agent has sub-agents with different models, apply GlobalGemini
only to agents using preview models:

```python
# Sub-agent with GA model — no fix needed
sub_agent = Agent(
    model=Gemini(model="gemini-2.5-flash"),
    ...
)

# Root agent with preview model — needs GlobalGemini
root_agent = Agent(
    model=GlobalGemini(model="gemini-3-flash-preview"),
    ...
    sub_agents=[sub_agent],
)
```

## Applying to Existing Agents (Migration)

When migrating an existing agent that uses the env var timing approach:

1. Add the `GlobalGemini` class to `agent.py`
2. Change `Gemini(...)` to `GlobalGemini(...)` in agent definition(s)
3. Remove `os.environ["GOOGLE_CLOUD_LOCATION"] = "global"` from `agent.py`
4. Remove ALL `GOOGLE_CLOUD_LOCATION` manipulation from `agent_engine_app.py`
5. Redeploy: `make deploy`
6. Test from Agent Engine Playground AND Gemini Enterprise (if registered)

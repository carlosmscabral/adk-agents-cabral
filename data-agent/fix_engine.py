import os
with open('app/agent_engine_app.py', 'r') as f:
    c = f.read()
import re
c = re.sub(r'agent_engine_id=os\.environ\.get\("GOOGLE_CLOUD_AGENT_ENGINE_ID"\)', r'agent_engine_id=os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID", "").split("/")[-1]', c)
with open('app/agent_engine_app.py', 'w') as f:
    f.write(c)

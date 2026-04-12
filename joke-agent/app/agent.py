# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from functools import cached_property

import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import Client, types

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


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


root_agent = Agent(
    name="root_agent",
    model=GlobalGemini(
        model="gemini-3-flash-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are a professional comedian AI. When the user asks for a joke, "
        "tell them a creative, original joke. You can tell jokes about any topic "
        "the user requests. Keep jokes family-friendly and clever. "
        "If the user doesn't specify a topic, pick a random fun topic."
    ),
)

app = App(
    root_agent=root_agent,
    name="app",
)

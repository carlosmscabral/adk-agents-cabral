# Specification: Live API Conversational Agent

## Overview
Implement a demo Google ADK Python agent that leverages the Gemini Live API for a conversational, full-voice (Audio In/Audio Out) experience. The demo will work locally via ADK Web and be deployable to Vertex AI Agent Engine. A React/Next.js Web Frontend will be created to interface with the Agent Engine backend, defining the protocol and interaction for a full conversational voice experience. The frontend deployment strategy will be determined after an initial architectural analysis.

## Functional Requirements
- **ADK Agent:** A Python-based ADK agent configured to use the Gemini Live API.
- **Capabilities:** The agent will include Google Search grounding as a tool to demonstrate real-time, grounded voice interactions.
- **Local Development:** The agent must be runnable locally using the `adk web` CLI command or a similar local testing harness.
- **Backend Deployment:** The agent must be configured for deployment to Vertex AI Agent Engine.
- **Web Frontend Application:** A React/Next.js frontend application must be developed to capture microphone input, stream it to the backend agent, and play back the audio responses.
- **Frontend Architecture & Deployment:** Evaluate and determine the optimal deployment strategy for the frontend (e.g., Cloud Run vs. Firebase Hosting) based on the streaming protocol, statefulness requirements, and architecture complexity.
- **Protocol:** Define and implement the streaming interaction protocol between the React frontend and the Agent Engine backend for the Live API.

## Non-Functional Requirements
- Uses Python `uv` for dependency management (`[tool.uv] package = false`).
- Models must be accessed exclusively via Vertex AI (`GOOGLE_GENAI_USE_VERTEXAI=1`).
- The frontend should be clean and clearly demonstrate the Live API connection.

## Acceptance Criteria
- [ ] The agent runs locally via ADK web or a local runner and accepts audio input/output.
- [ ] The agent can successfully execute a Google Search tool call during a voice conversation.
- [ ] The agent is successfully deployed to Vertex AI Agent Engine.
- [ ] A documented architectural decision is made regarding the frontend deployment strategy (Cloud Run vs Firebase Hosting).
- [ ] The Next.js frontend is deployed via the chosen strategy and successfully connects to the Agent Engine backend to capture user voice and play back the agent's voice response with low latency.

## Out of Scope
- Production-grade authentication for the frontend (beyond what's necessary for the demo).
- Persistent conversation history across multiple disparate sessions (focus is on the live streaming session).
- Additional complex tool calling beyond Google Search.

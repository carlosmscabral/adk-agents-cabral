# Implementation Plan: Live API Conversational Agent

## Phase 1: Agent Setup and Local Verification
- [ ] Task: Initialize ADK Project
    - [ ] Create folder for the new agent demo (e.g., `live_api_agent/`).
    - [ ] Set up `pyproject.toml` with `uv` (`[tool.uv] package = false`) and required dependencies (`google-adk`, etc.).
    - [ ] Set up environment template (`.env.template`) with `GOOGLE_GENAI_USE_VERTEXAI=1`.
- [ ] Task: Implement Live API Agent
    - [ ] Create core agent logic using `google-adk` configured for the Gemini Live API.
    - [ ] Integrate the Google Search tool for grounding into the agent.
- [ ] Task: Create Local Testing Script
    - [ ] Create a `run_agent.py` script to programmatically interact with the agent via terminal (text-based testing of the logic).
    - [ ] Verify agent logic and tool execution (Google Search) locally.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Agent Setup and Local Verification' (Protocol in workflow.md)

## Phase 2: Web Frontend and Protocol Architecture
- [ ] Task: Architectural Analysis
    - [ ] Define the streaming interaction protocol (e.g., WebSockets, Server-Sent Events) between the frontend and the Agent Engine backend.
    - [ ] Evaluate statefulness requirements.
    - [ ] Document the decision on the frontend deployment strategy: Cloud Run vs. Firebase Hosting.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Web Frontend and Protocol Architecture' (Protocol in workflow.md)

## Phase 3: Frontend Implementation
- [ ] Task: Initialize React/Next.js Project
    - [ ] Bootstrap the Next.js frontend application.
    - [ ] Set up basic UI/UX for capturing and playing voice.
- [ ] Task: Implement Audio Streaming & Protocol
    - [ ] Implement browser microphone capture and audio playback.
    - [ ] Implement the defined connection protocol to interface with the ADK backend.
- [ ] Task: Integration Testing
    - [ ] Connect the local React frontend to the local ADK agent instance.
    - [ ] Verify full voice (Audio In/Out) round-trip functionality.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Frontend Implementation' (Protocol in workflow.md)

## Phase 4: Deployment
- [ ] Task: Deploy Backend
    - [ ] Configure and deploy the ADK agent to Vertex AI Agent Engine.
- [ ] Task: Deploy Frontend
    - [ ] Configure and deploy the frontend application based on the architectural decision from Phase 2 (Cloud Run or Firebase Hosting).
- [ ] Task: End-to-End Verification
    - [ ] Test the fully deployed solution to ensure low-latency voice interaction and correct tool usage.
- [ ] Task: Update Root README
    - [ ] Update the repository's main `README.md` with a link to the newly created demo and a brief description (per Track Finalization Protocol).
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Deployment' (Protocol in workflow.md)
\n## Phase 5: Review Fixes\n- [x] Task: Apply review suggestions f7c621e

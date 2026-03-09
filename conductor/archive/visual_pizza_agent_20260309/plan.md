# Implementation Plan: visual_pizza_agent

## Phase 1: Project Setup and Boilerplate
- [x] Task: Copy base project structure from `live_api_pizza`.
    - [x] Sub-task: Duplicate `backend` and `frontend` folders into `visual_pizza_agent`.
    - [x] Sub-task: Update `pyproject.toml` and `package.json` names to reflect `visual_pizza_agent`.
    - [x] Sub-task: Update backend entry points (`run_agent.py`, `api_server.py`) and connection URLs in the frontend to point to the new service if applicable.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Project Setup and Boilerplate' (Protocol in workflow.md)

## Phase 2: Backend Implementation - Image Tool & Agent Update
- [x] Task: Implement `generate_pizza_image` tool.
    - [x] Sub-task: Create `tools.py` in the backend app directory.
    - [x] Sub-task: Write `generate_pizza_image` function using `google.genai.Client` and `imagen-3.0-generate-002`, forcing a "realistic photo" style in the prompt.
    - [x] Sub-task: Ensure the tool returns the base64 image data or an identifier the frontend can parse.
- [x] Task: Update the core Agent definition.
    - [x] Sub-task: Import and add `generate_pizza_image` to the agent's `tools` list in `agent.py`.
    - [x] Sub-task: Modify the agent's `instruction` to explicitly call the image generation tool upon concluding the order.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Backend Implementation - Image Tool & Agent Update' (Protocol in workflow.md)

## Phase 3: Frontend Implementation - Image Rendering
- [x] Task: Update the Next.js WebSocket message handler in `page.tsx`.
    - [x] Sub-task: Add parsing logic to intercept payloads containing the generated image (e.g., from the tool call response sent down the socket).
    - [x] Sub-task: Update the `messages` state to include an image block when received.
- [x] Task: Update the chat UI component.
    - [x] Sub-task: Render an `<img>` tag with the base64 data inside the relevant message bubble.
    - [x] Sub-task: Ensure proper styling and responsive bounds for the inline image.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Frontend Implementation - Image Rendering' (Protocol in workflow.md)
# Specification: visual_pizza_agent

## Overview
Create a `visual_pizza_agent` that extends the interactive voice-based pizza ordering experience (based on `@live_api_pizza`) by dynamically generating a realistic image of the final pizza once the order is complete.

## Functional Requirements
**1. Agent Backend**
- Create a new project directory `visual_pizza_agent` structure similar to `live_api_pizza`.
- The agent utilizes `gemini-live-2.5-flash-native-audio` to maintain the energetic Italian chef persona.
- Integrate a new ADK tool, `generate_pizza_image(description: str)`, utilizing the `imagen-3.0-generate-002` model via `google.genai.Client`.
- The prompt should enforce that the image style is "Realistic Photo".
- The agent is instructed to automatically trigger this tool when the user finalizes their pizza creation.

**2. Frontend (Next.js/React)**
- Maintain the same WebSocket connection logic for audio streaming.
- Extend the frontend message handling to detect image payloads (e.g., base64 data or URLs returned by the tool execution or custom server events).
- Render the generated pizza image inline within the chat interface as a new message bubble.

## Non-Functional Requirements
- **Performance:** Ensure image generation and transfer do not severely block or disrupt the ongoing voice connection.
- **Code Reuse:** Reuse as much boilerplate from `@live_api_pizza` as possible to speed up development.

## Acceptance Criteria
- User can converse with the agent using voice to build a pizza.
- Upon completion of the order, the agent autonomously generates an image of the pizza.
- The frontend successfully receives the image data and displays it inline in the chat history.
- The image matches the user's requested ingredients and has a realistic photographic style.

## Out of Scope
- Permanent cloud storage of generated images (in-memory or base64 over WebSocket is sufficient for the demo).
- Complex UI overhauls; the image will simply be appended to the existing chat flow.
# Tech Stack

This document outlines the core technologies, frameworks, and deployment targets for the ADK demo agents.

## Core Language & SDK
- **Language:** Python
- **SDK:** Google Agent Development Kit (ADK) (`google-adk`)
- **Voice & Streaming:** Gemini Live API for real-time bidirectional audio/text.
- **Image Processing:** **Pillow** for optimizing multi-modal outputs (e.g., resizing generated images).
- **Dependency Management:** `uv` (Fast Python package and project manager).
 All agent projects **must use `pyproject.toml`** as their primary dependency manifest. Because these demo agents are standalone executable applications rather than installable Python libraries, the `pyproject.toml` must include `[tool.uv] package = false` (or omit the `[build-system]` section) to prevent local editable build errors during `uv sync`. Local setups should be initialized using `uv sync` to ensure isolated and reproducible `.venv` environments. Auxiliary services (like mock APIs in subdirectories) may use `requirements.txt` if preferred for simpler containerization.

## Model Providers
- **Primary Models:** Google Gemini Models exclusively via Vertex AI integration (`GOOGLE_GENAI_USE_VERTEXAI=1`). Google AI Studio API Keys must not be used.

## Infrastructure & Deployment
*Deployment targets will vary based on the specific demo's use case, but may include:*
- **Google Cloud Run:** For containerized web endpoints and generic hosting.
- **Vertex AI Agent Engine:** For managed agent scaling and orchestration.
- **Data & Tools:** AlloyDB, BigQuery, and GCS integrations.
- **State Management:** Prioritize `InMemorySessionService` for standard demos to reduce friction, unless a persistent backend is specifically required.

## Ecosystem Tools & Extensions
*The demos will keep an open architecture, frequently showcasing integrations such as:*
- **Model Context Protocol (MCP):** Using `MCPToolset` to connect external data sources.
- **API Exposure:** FastAPI via `adk api_server` for exposing agents as standard REST endpoints.
- **Extensibility:** Open to wrapping tools from other ecosystems (LangChain, CrewAI, etc.) as needed per demo.

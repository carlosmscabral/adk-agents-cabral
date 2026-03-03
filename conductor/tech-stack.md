# Tech Stack

This document outlines the core technologies, frameworks, and deployment targets for the ADK demo agents.

## Core Language & SDK
- **Language:** Python
- **SDK:** Google Agent Development Kit (ADK) (`google-adk`)
- **Dependency Management:** `uv` (Fast Python package and project manager)

## Model Providers
- **Primary Models:** Google Gemini Models (e.g., `gemini-2.5-flash`, `gemini-2.5-pro`) via native integration.

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

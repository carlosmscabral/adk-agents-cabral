# ADK Agents Demo Repository

This repository contains a collection of sample agents built with the [Google Agent Developer Kit (ADK)](https://github.com/GoogleCloudPlatform/adk-python). These examples demonstrate various patterns, integrations, and deployment strategies for AI agents on Google Cloud.

## Not Google Product Clause

This is not an officially supported Google product, nor is it part of an official Google product.

## Agents

The table below lists the finalized agents available in this repository:

| Agent / Track | Description | Link |
| --- | --- | --- |
| **External OAuth/OIDC Tool Authentication Flow** | Demonstrates how to build an ADK Python agent that securely consumes externally generated OAuth/OIDC access tokens (e.g., from Keycloak) via Gemini Enterprise (AgentSpace). | [external_oauth_agent](./external_oauth_agent/) |
| **Live API Conversational Pizza Agent** | Demonstrates bidirectional streaming (bidi) voice interactions using the Gemini Live API. Features a custom FastAPI backend running on Cloud Run and a React frontend utilizing Web Audio API for real-time PCM audio streaming. | [live_api_pizza](./live_api_pizza/) |

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for details.

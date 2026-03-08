FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml .
# If you had uv.lock, copy it too
# COPY uv.lock .

# Install dependencies using uv
RUN uv sync --no-cache

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 8080

# Environment variables (to be overridden at runtime)
ENV GOOGLE_GENAI_USE_VERTEXAI=TRUE
ENV GOOGLE_CLOUD_LOCATION=us-central1
ENV PORT=8080

# Run the custom FastAPI server
CMD ["uv", "run", "uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]

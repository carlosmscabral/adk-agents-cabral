# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.12-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME

# Copy only the files needed for the API
COPY api_server/ ./api_server/

# Install dependencies from the API's requirements file
RUN pip install --no-cache-dir -r api_server/requirements.txt

# Run the web service on container startup using uvicorn.
# Port is provided by Cloud Run.
CMD ["uvicorn", "api_server.main:app", "--host", "0.0.0.0", "--port", "8080"]

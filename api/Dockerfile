FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Docker CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app
COPY ./scripts ./scripts
COPY ./static ./app/static
COPY ./entrypoint.sh /app/entrypoint.sh

# Create logs directory
RUN mkdir -p /app/logs

# Create tmp directory for builds with secure permissions
RUN mkdir -p /app/tmp && chmod 755 /app/tmp

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# NOTE: Running as root is required for Docker socket access inside the container.
# If you need to run as non-root, you must ensure the docker socket is group-accessible and the group id matches.
# For public/production, consider using a build service or a privileged sidecar.

# (No USER appuser, run as root for Docker access)

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/ping || exit 1

# Run the application (this will be passed to entrypoint.sh)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM python:3.12

ENV PYTHONUNBUFFERED=1

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

# Install dependencies first for better caching
COPY pyproject.toml uv.lock* /app/
RUN uv sync --frozen --no-dev --no-install-project

# Add uvloop for Linux performance
RUN uv add uvloop

COPY . /app

# Final sync to install the project itself
RUN uv sync --frozen --no-dev

# Ensure start.sh is executable
RUN chmod +x /app/start.sh

# Entrypoint to shell script
CMD ["/bin/bash", "/app/start.sh"]

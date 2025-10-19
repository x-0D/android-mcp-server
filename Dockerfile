FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ADB_VERSION=34.0.4

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    unzip \
    wget \
    android-sdk-platform-tools-common \
    libc6 \
    libgcc1 \
    && rm -rf /var/lib/apt/lists/*

# Download and install Android SDK Platform-Tools (ADB)
RUN wget -q https://dl.google.com/android/repository/platform-tools_r${ADB_VERSION}-linux.zip -O /tmp/platform-tools.zip \
    && unzip -q /tmp/platform-tools.zip -d /tmp/ \
    && mv /tmp/platform-tools/adb /usr/local/bin/ \
    && mv /tmp/platform-tools/fastboot /usr/local/bin/ \
    && rm -rf /tmp/platform-tools* \
    && chmod +x /usr/local/bin/adb /usr/local/bin/fastboot

# Verify ADB installation (client-only, no server required)
RUN adb version

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY server.py adbdevicemanager.py ./

# Install Python deps (editable install). Adjust if your project requires build tools.
RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --no-cache-dir -e .

# Create a non-root user for security and set ownership
RUN useradd -m -u 1000 android && \
    chown -R android:android /app

# Create entrypoint that starts adb server before launching the app
RUN echo '#!/bin/sh\nset -e\n# start adb server (ignore failure)\nadb start-server || true\n# short wait for adb to bind socket\nsleep 1\n# exec passed command\nexec "$@"' > /usr/local/bin/docker-entrypoint.sh && \
    chmod +x /usr/local/bin/docker-entrypoint.sh && \
    chown root:root /usr/local/bin/docker-entrypoint.sh

 USER android

# Expose port for HTTP endpoint
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD adb version || exit 1

# Run the MCP server with both HTTP transports; entrypoint ensures adb server is started
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "server.py", "--transport", "all", "--host", "0.0.0.0", "--port", "8000"]

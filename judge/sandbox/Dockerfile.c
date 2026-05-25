FROM gcc:12-bookworm

# Create unprivileged user and make workspace accessible to nobody
RUN groupadd -r judge && \
    useradd -r -g judge -m -s /bin/bash judge && \
    mkdir -p /workspace && \
    chown -R nobody:nogroup /workspace && \
    chmod 777 /workspace

# Install cJSON library (needed for JSON parsing in C driver)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcjson-dev \
    && rm -rf /var/lib/apt/lists/*

USER judge
WORKDIR /workspace

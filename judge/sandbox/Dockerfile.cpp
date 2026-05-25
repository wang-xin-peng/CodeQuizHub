FROM gcc:12-bookworm

# Create unprivileged user and make workspace accessible to nobody
RUN groupadd -r judge && \
    useradd -r -g judge -m -s /bin/bash judge && \
    mkdir -p /workspace && \
    chown -R nobody:nogroup /workspace && \
    chmod 777 /workspace

# Install cJSON and nlohmann-json libraries (needed for JSON parsing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcjson-dev \
    nlohmann-json3-dev \
    && rm -rf /var/lib/apt/lists/*

USER judge
WORKDIR /workspace

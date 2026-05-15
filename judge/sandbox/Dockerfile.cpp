FROM gcc:12-bookworm

# Create unprivileged user
RUN groupadd -r judge && \
    useradd -r -g judge -m -s /bin/bash judge && \
    mkdir -p /workspace && \
    chown judge:judge /workspace

# Install cJSON library (needed for JSON parsing in C++ driver)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcjson-dev \
    && rm -rf /var/lib/apt/lists/*

USER judge
WORKDIR /workspace

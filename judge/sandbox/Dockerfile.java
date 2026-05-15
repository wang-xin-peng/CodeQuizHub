FROM openjdk:17-slim

# Create unprivileged user
RUN groupadd -r judge && \
    useradd -r -g judge -m -s /bin/bash judge && \
    mkdir -p /workspace && \
    chown judge:judge /workspace

# Install JSON library for parsing judge input
RUN apt-get update && apt-get install -y --no-install-recommends wget ca-certificates && \
    wget -q -O /workspace/json.jar \
    https://repo1.maven.org/maven2/org/json/json/20231013/json-20231013.jar && \
    chown judge:judge /workspace/json.jar && \
    apt-get remove -y wget ca-certificates && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

USER judge
WORKDIR /workspace

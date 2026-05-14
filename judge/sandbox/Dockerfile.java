FROM openjdk:17-slim

RUN useradd -m -s /bin/bash judge && \
    mkdir -p /workspace && \
    chown judge:judge /workspace

# Download json.jar for JSON handling in judge
RUN apt-get update && apt-get install -y --no-install-recommends wget && \
    wget -q -O /workspace/json.jar https://repo1.maven.org/maven2/org/json/json/20231013/json-20231013.jar && \
    chown judge:judge /workspace/json.jar && \
    apt-get remove -y wget && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

USER judge
WORKDIR /workspace

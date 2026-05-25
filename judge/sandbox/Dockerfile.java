FROM eclipse-temurin:17-jdk-jammy

# Download JSON library for test I/O
RUN apt-get update && apt-get install -y \
        wget \
        ca-certificates && \
    mkdir -p /workspace && \
    wget -q -O /workspace/json.jar \
        https://repo1.maven.org/maven2/org/json/json/20231013/json-20231013.jar && \
    apt-get remove -y wget ca-certificates && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    javac -version && java -version

# Create unprivileged user and make workspace accessible to nobody
RUN groupadd -r judge && \
    useradd -r -g judge -m -s /bin/bash judge && \
    chown -R nobody:nogroup /workspace && \
    chmod 777 /workspace

USER judge
WORKDIR /workspace

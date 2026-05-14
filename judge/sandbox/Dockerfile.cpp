FROM gcc:12

RUN useradd -m -s /bin/bash judge && \
    mkdir -p /workspace && \
    chown judge:judge /workspace

USER judge
WORKDIR /workspace

FROM debian:bookworm-slim

ARG BUILD_VERSION="dev"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        jq \
        tar \
        libatomic1 \
    && rm -rf /var/lib/apt/lists/*

COPY run.sh /run.sh
RUN chmod 0755 /run.sh

LABEL \
    io.hass.type="app" \
    io.hass.version="${BUILD_VERSION}" \
    org.opencontainers.image.title="Spotify Soloist for Home Assistant" \
    org.opencontainers.image.description="Home Assistant app wrapper for Spotify Soloist" \
    org.opencontainers.image.licenses="MIT"

CMD ["/run.sh"]

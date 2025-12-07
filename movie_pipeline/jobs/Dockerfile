FROM cronicle/edge:latest AS builder

FROM fripiane/movie_pipeline:0.2.13 AS runtime

# Include `movie_pipeline` to `cronicle_edge`
# cf https://github.com/cronicle-edge/cronicle-edge/blob/main/Dockerfile

RUN apt-get update \
    && apt-get install -y bash tini util-linux bash openssl procps coreutils curl tar jq \
    && rm -rf /var/lib/apt/lists/*

# Install up-to date node version
RUN curl -fsSL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh \
    && bash nodesource_setup.sh \
    && rm nodesource_setup.sh \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && node -v

# non root user for shell plugin
ARG CRONICLE_UID=1000
ARG CRONICLE_GID=1099
RUN addgroup cronicle --gid "$CRONICLE_GID" && adduser -D -h /opt/cronicle -u "$CRONICLE_UID" -G cronicle cronicle

COPY --from=builder /opt/cronicle /opt/cronicle

ENV PATH="/opt/cronicle/bin:${PATH}"
ENV CRONICLE_foreground=1
ENV CRONICLE_echo=1
ENV TZ=Europe/Paris 

WORKDIR /opt/cronicle 

# protect sensitive folders
RUN  mkdir -p /opt/cronicle/data /opt/cronicle/conf && chmod 0700 /opt/cronicle/data /opt/cronicle/conf

ENTRYPOINT ["/usr/bin/tini", "--"]
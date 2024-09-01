
FROM python:3.11.9 AS builder
RUN pip install poetry==1.7.1

ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

RUN mkdir /app
COPY pyproject.toml poetry.lock* README* /app/
COPY ./movie_pipeline /app/movie_pipeline
RUN cd /app && poetry build -f wheel


FROM borda/docker_python-opencv-ffmpeg:gpu-py3.11-cv4.10.0 AS runtime

LABEL org.opencontainers.image.title=movie_pipeline
LABEL org.opencontainers.image.version=0.2.7
LABEL org.opencontainers.image.authors=['GdPaul1234 <paul.godin1234@outlook.fr>']
LABEL org.opencontainers.image.licenses=
LABEL org.opencontainers.image.url=
LABEL org.opencontainers.image.source=

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y tini \
    && rm -rf /var/lib/apt/lists/*

# Remove conflicting package
RUN apt-get remove -y python3-blinker

WORKDIR /app
COPY --from=builder /app/dist/ /app/dist/

RUN pip install dist/movie_pipeline-0.2.7-py3-none-any.whl \
    && rm -rf /app/dist/

# Init movie_pipeline directories
RUN mkdir -p inputs movies series backup logs archive/source archive/dest /root/.movie_pipeline \
    && touch /root/.movie_pipeline/config.env \
    && touch logs/log.txt

ENV Paths__movies_folder=/app/movies
ENV Paths__series_folder=/app/series
ENV Paths__backup_folder=/app/backup

ENV Archive__base_backup_path=/app/archive/source
ENV Archive__movies_archive_folder=/app/archive/dest
ENV Archive__max_retention_in_s=33_000_000

ENV Logger__file_path=/app/logs/log.txt

# Expose port of the mpire-dashboard
EXPOSE 8080

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["movie_pipeline", "--help"]

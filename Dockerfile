
FROM python:3.13.10 AS builder
RUN pip install poetry==2.2.1

ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

RUN mkdir /app
COPY pyproject.toml README* /app/

# replace opencv-contrib-python dependency by opencv-contrib-python-headless
RUN sed -i 's/opencv-contrib-python/opencv-contrib-python-headless/g' /app/pyproject.toml

COPY ./movie_pipeline /app/movie_pipeline
RUN cd /app && poetry build -f wheel


FROM linuxserver/ffmpeg:version-8.0-cli AS runtime

LABEL org.opencontainers.image.title=movie_pipeline
LABEL org.opencontainers.image.version=0.2.12
LABEL org.opencontainers.image.authors=['GdPaul1234 <paul.godin1234@outlook.fr>']
LABEL org.opencontainers.image.licenses=
LABEL org.opencontainers.image.url=
LABEL org.opencontainers.image.source=

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y python3-pip tini \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 --version

WORKDIR /app
COPY --from=builder /app/dist/ /app/dist/

# Install and verify movie_pipeline installation
ARG PIP_BREAK_SYSTEM_PACKAGES=1
ARG PIP_NO_CACHE_DIR=1 
RUN pip3 install dist/movie_pipeline-0.2.12-py3-none-any.whl \
    && movie_pipeline --help

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

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["movie_pipeline", "--help"]

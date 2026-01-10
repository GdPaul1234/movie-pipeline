
FROM python:3.13.11 AS builder
RUN pip install poetry==2.2.1

ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

RUN mkdir /app
COPY --from=movie_pipeline pyproject.toml README* /app/

# replace opencv-contrib-python dependency by opencv-contrib-python-headless
RUN sed -i 's/opencv-contrib-python/opencv-contrib-python-headless/g' /app/pyproject.toml

COPY --from=movie_pipeline ./movie_pipeline /app/movie_pipeline
RUN cd /app && poetry build -f wheel


FROM ghcr.io/pixlcore/xysat:latest AS runtime

ARG VERSION=0.2.14

LABEL org.opencontainers.image.title=movie_pipeline_xysat
LABEL org.opencontainers.image.version=$VERSION
LABEL org.opencontainers.image.authors=['GdPaul1234 <paul.godin1234@outlook.fr>']
LABEL org.opencontainers.image.licenses=
LABEL org.opencontainers.image.url=
LABEL org.opencontainers.image.source=

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY --from=builder /app/dist/ /app/dist/

# Install ffmpeg
ARG FFMPEG_VARIANT=ffmpeg-n8.0-latest-linux64-gpl-shared-8.0
ADD --unpack=true --exclude=doc/* --exclude=man/** \
    https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/$FFMPEG_VARIANT.tar.xz \
    /opt
RUN ln -s /opt/$FFMPEG_VARIANT/lib/* /usr/local/lib/ \
    && ldconfig \
    && ln -s /opt/$FFMPEG_VARIANT/bin/* /usr/local/bin/ \
    && ffmpeg -version \
    && ffprobe -version

# Install and verify movie_pipeline installation
RUN ~/.local/bin/uv tool install dist/movie_pipeline-0.2.14-py3-none-any.whl \
    && ln -s ~/.local/bin/* /usr/local/bin/ \
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

WORKDIR /opt/xyops/satellite
CMD ["sh", "container-start.sh"]

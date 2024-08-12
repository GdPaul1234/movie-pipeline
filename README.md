# Movie Pipeline

Set of tools that automatize most of movies library maintenance

**This program is distributed WITHOUT ANY WARRANTY, use AT YOUR OWN RISK.**

## Usage

```
$ python app.py --help

 Usage: app.py [OPTIONS] COMMAND [ARGS]...

 Available commands:

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --log-level                 [debug|info|warning|error|critical]  [default: info]                                     │
│ --config-path               PATH                                 Config path                                         │
│                                                                  [default:                                           │
│                                                                  C:\Users\paulg\.movie_pipeline\config.env]          │
│ --install-completion                                             Install completion for the current shell.           │
│ --show-completion                                                Show completion for the current shell, to copy it   │
│                                                                  or customize the installation.                      │
│ --help                                                           Show this message and exit.                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ archive_movies             Archive movies regarding options in config file                                           │
│ detect_segments            Run best-effort segments detectors                                                        │
│ process_movie              Cut and merge movie segments to keep only relevant part                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Running locally

Install poetry, then run:

```sh
poetry build -f wheel
pip install --user ./dist/movie_pipeline-${VERSION}-py3-none-any.whl
```

The following commands will be available:

```sh
movie_pipeline
movie_pipeline_job_archive_movies
movie_pipeline_job_detect_segments
movie_pipeline_job_process_movie
```

### Running with docker

Build the movie_pipeline project:

```sh
docker build -t fripiane/movie_pipeline:0.2.6 .
```

Then build the cronicle integration:

```sh
docker build -t fripiane/movie_pipeline_cronicle:${VERSION} ./movie_pipeline/jobs/
```

Create and fill in the `.env` file:

```env
paths_base_path=V:\PVR
archive_base_backup_path=W:\Dossier personnel\video

PATHS_INPUT_FOLDER=${paths_base_path}

PATHS_MOVIES_FOLDER=${paths_base_path}\Films
PATHS_SERIES_FOLDER=${paths_base_path}\Séries
PATHS_BACKUP_FOLDER=${archive_base_backup_path}\PVR\playground

ARCHIVE_BACKUP_FOLDER=W:\Dossier personnel\video
ARCHIVE_MOVIES_ARCHIVE_FOLDER=${archive_base_backup_path}\Films
LOGGER_LOG_FOLDER=${paths_base_path}

CRONICLE_secret_key=
```

Then run:

```sh
docker compose up
```

## Configuration

Before using this program, you must provide a valid config file.

You can find many of them in the `tests` directory.

If no `--config-path` is empty, the app will fallback to `~/.movie_pipeline/config.env` file.

> [!NOTE]
> Relative path is resolved from the config folder. Older config MIGHT break.

> [!WARNING]
> There is a breaking change with the configuration format to ensure runtime validation with Pydantic and python-dotenv

You can find bellow an example of the old format:

```ini
[Paths]
base_path=V:\PVR
base_backup_path=W:\Dossier personnel\video

movies_folder=${base_path}\Films
series_folder=${base_path}\Séries

backup_folder=${base_backup_path}\PVR\playground
movies_archive_folder=${base_backup_path}\Films
series_archive_folder=${base_backup_path}\Séries

title_strategies=.\title_strategies.yml
title_re_blacklist=.\title_re_blacklist.txt

[Archive]
max_retention_in_s=31_104_000

[SegmentDetection]
templates_path=V:\PVR\autres\scripts\common-ressources\logo

[Processor]
nb_worker=2

[Logger]
file_path=${Paths:base_path}\log.txt
```

The equivalent in the newer format is:

```env
Paths__base_path=V:\PVR
Archive__base_backup_path=W:\Dossier personnel\video

Paths__movies_folder=${Paths__base_path}\Films
Paths__series_folder=${Paths__base_path}\Séries
Paths__backup_folder=${Archive__base_backup_path}\PVR\playground

Archive__movies_archive_folder=${Archive__base_backup_path}\Films
Archive__max_retention_in_s=31_104_000

Paths__title_strategies=.\title_strategies.yml
Paths__title_re_blacklist=.\title_re_blacklist.txt

SegmentDetection__templates_path=V:\PVR\autres\scripts\common-ressources\logo

Processor__nb_worker=2

Logger__file_path=${Paths__base_path}\log.txt
```

## Main commands

### Basic workflow: detect and trim relevant segments + move to media library

Once the configuration file has been filled in and all registrations made:

- **RECOMMENDED**. Run sequentially :
  1. The `detect_segments` command to prefill the relevant segments to be kept for a given movie

  2. `python segment_validator` after downloading and installing the
     [movie_pipeline_segments_validator](https://github.com/GdPaul1234/movie-pipeline-segments-validator) tool.
     It will create an edit decision file after you review and validate the releant segments to be kept.

Alternatively, you can manually populate each edit decision file according to the following rules:

1. Scaffold the recording. For each media, fill in the editing decision file (`.yml.txt` files) by:
    - Correcting the title if necessary, especially for Series.

      _For reference, the format of the series title is as follows: `Serie Name S01E02.mp4`_

    - Using a third-party software or the built-in `detect_segments` command to fill in the segments to be kept.

      _i.e. `00:31:53.960-01:00:51.520,01:06:54.480-01:31:40.160,01:37:34.480-02:23:05.560,`_

      Don't forget to:
        1. Carrefuly review the segments field
        2. Append the leading comma at the end to validate your result!

    - Add `skip_backup: yes` line if the movie file is too big (more than 10 Go).

2. Process movie (cut, trim, convert movies, backup and move them to the right location) by running the `process_movie` command

> [!WARNING]
> The current implementation of `backup_policy_executor` deletes the original file if is identified as a **serie**.
> Be sure that you have some kind of recycle bin puts in place in your system, so the deleted file is moved inside it
> instead of being definitly deleted.

### Archive medias

If the remaining space of `base_path` is low, use the `archive_movies` command.

> [!WARNING]
> It takes for granted that you periodicaly backup each movies (located in `movies_folder`) to `${base_backup_path}/PVR/Films`.

This command is mainly created for my needs, don't run it if you don't have a movie backup in place as it deletes
the oldest movies in `base_path` and move the corresponding `${base_backup_path}/PVR/Films` to `movies_archive_folder`.

Only movies are supported at the time of writing this document.

## TODO

- Improve segments detection, auto selection of the best strategies
- Add more tests for segment detections

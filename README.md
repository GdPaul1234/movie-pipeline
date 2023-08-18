# Movie Pipeline

Set of tools that automatize most of movies library maintenance

**This program is distributed WITHOUT ANY WARRANTY, use AT YOUR OWN RISK.**

## Usage

```
$ python app.py --help
usage: app.py [-h] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--config-path CONFIG_PATH]
              {legacy_move,process_movie,scaffold_dir,archive_movies,dump_for_kodi,detect_segments,validate_dir,update_media_database,launch_media_dashboard}
              ...

positional arguments:
  {legacy_move,process_movie,scaffold_dir,archive_movies,dump_for_kodi,detect_segments,validate_dir,update_media_database,launch_media_dashboard}
                        Available commands:
    legacy_move         Move converted movies or series to their folder
    process_movie       Cut and merge movie segments to keep only relevant parts
    scaffold_dir        Scaffold movie edit decision files
    archive_movies      Archive movies regarding options in config file
    dump_for_kodi       Dump .vsmeta to .nfo if not exist
    detect_segments     Run best-effort segments detectors
    validate_dir        Validate segments and generate edit decision files in given directory
    update_media_database
                        Update media database from NFOs for further analysis
    launch_media_dashboard
                        Launch grafana dashboard provisioned with media stats dashboard

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
  --config-path CONFIG_PATH
                        Config path
```

## Configuration

Before using this program, you must provide a valid config file.

You can find many of them in the `tests` directory.

If no `--config-path` is empty, the app will fallback to `config.env` file in the current directory.

> **Warning**
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

Logger__file_path=${Paths__base_path}\log-quick.txt
```

## Main commands

### Basic workflow: detect and trim relevant segments + move to library

Once the configuration file has been filled in and all registrations made:

- **RECOMMENDED**. Run sequentially the `detect_segments` command and the `validate_dir` command to pre-fill and validate each edit decision file on the left panel of the Seegment reviewer window.

Alternatively, you can manually populate each edit decision file according to the following rules:

1. Scaffold the recording directory using the command `scaffold_dir`

2. Fill in the editing decision file (`.yml.txt` files) by:
    - Correcting the title if necessary, especially for Series.

      _For reference, the format of the series title is as follows: `Serie Name S01E02.mp4`_

    - Using a third-party software or the built-in `detect_segments` command to fill in the segments to be kept.

      _i.e. `00:31:53.960-01:00:51.520,01:06:54.480-01:31:40.160,01:37:34.480-02:23:05.560,`_

      Don't forget to:
        1. Carrefuly review the segments field
        2. Append the leading comma at the end to validate your result!

    - Add `skip_backup: yes` line if the movie file is too big (more than 10 Go).

3. Process movie (cut, trim, convert movies, backup and move them to the right location) by running the `process_movie` command

> **Warning**
> The current implementation of `backup_policy_executor` deletes the original file if is identified as a **serie**.
> Be sure that you have some kind of recycle bin puts in place in your system, so the deleted file is moved inside it
> instead of being definitly deleted.

### Archive pipeline

If the remaining space of `base_path` is low, use the `archive_movies` command.

> **Warning**
> It takes for granted that you periodicaly backup each movies (located in `movies_folder`) to `${base_backup_path}/PVR/Films`.

This command is mainly created for my needs, don't run it if you don't have a movie backup in place as it deletes
the oldest movies in `base_path` and move the corresponding `${base_backup_path}/PVR/Films` to `movies_archive_folder`.

Only movies are supported at the time of writing this document.

### Dump for kodi

This command converts `.vsmeta` dumped metadata to the kodi `.nfo` format.

It is useful for quickly setting up a kodi media library in an external storage.

### Basic statistics about media library

You can run the `update_media_database` and the `launch_media_dashboard` commands to have a nice dashboard that aggregate
many interesting facts about your media liberay.

You must have docker installed in order to use the `launch_media_dashboard`.

Don't forget to fill in the `MediaDatabase__db_path` field in your `.env`.

## TODO

- Improve segments detection, auto selection of the best strategies
- Add tests for GUI and segment detections

# Movie Pipeline

Set of tools that automatize most of movies library maintenance

**This program is distributed WITHOUT ANY WARRANTY, use AT YOUR OWN RISK.**

## Usage

```
$ python app.py --help
usage: app.py [-h] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--config-path CONFIG_PATH]
              {legacy_move,process_movie,scaffold_dir,archive_movies,dump_for_kodi,detect_segments,validate_dir} ...

positional arguments:
  {legacy_move,process_movie,scaffold_dir,archive_movies,dump_for_kodi,detect_segments,validate_dir}
                        Available commands:
    legacy_move         Move converted movies or series to their folder
    process_movie       Cut and merge movie segments to keep only relevant parts
    scaffold_dir        Scaffold movie edit decision files
    archive_movies      Archive movies regarding options in config file
    dump_for_kodi       Dump .vsmeta to .nfo if not exist
    detect_segments     Run best-effort segments detectors
    validate_dir        Validate segments and generate edit decision files in given directory

options:
  -h, --help            show this help message and exit
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
  --config-path CONFIG_PATH
                        Config path
```

## Configuration

Before using this program, you must provide a valid config file.

You can find many of them in the `tests` directory.

If no `--config-path` is empty, the app will fallback to `config.ini` file in the current directory.

You can find bellow an example:

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

## Pipelines

### Main pipeline

After filling the config file and after all recordings are done:

1. Scaffold the recording directory using the command `scaffold_dir`

2. Fill the edit decision file (`.yml.txt` files) by:
    - Correcting the title if necessary, especially for Series.

      For reference, the format of series are: `Serie Name S01E02.mp4`

    - Using a third-party software or built-in `detect_segments` (beta) command to fill the segments to keep field

      ie. `00:31:53.960-01:00:51.520,01:06:54.480-01:31:40.160,01:37:34.480-02:23:05.560,`.

      Don't forget to carrefuly review the segments field and to append the leading comma at the end to validate your result!

      > INFO You can use the built-in `validate_dir` commands to validate segments from all completed movies that have been analyzed by the `detect_segments` command

    - Add `skip_backup: yes` line if the movie file is too big (more than 10 Go).

3. Process movie (cut, trim, convert movies, backup and move them to the right location) by running the `process_movie` command

  > WARNING
  > The current implementation of `backup_policy_executor` deletes the original file if is identified as a **serie**.
  > Be sure that you have some kind of recycle bin puts in place in your system, so the deleted file is moved inside it
  > instead of being definitly deleted.

### Archive pipeline

If the remaining space of the `base_path` is low, use the `archive_movies` command.

> WARNING
> it takes for granted that you periodicaly backup each movies (located in `movies_folder`) to `${base_backup_path}/PVR/Films`.

This command are primarly created to fit my need, don't run it if you don't have movies backup in place because it deletes the oldest movies in `base_path` and move the corresponding `${base_backup_path}/PVR/Films` to `movies_archive_folder`.

Only movies are supported at the time of writing this document

### Dump for kodi

This pipeline converts `.vsmeta` dumped metadata to the kodi `.nfo` format.

Useful for quickly set up kodi media library in external storage.

## TODO

- Improve segments detection, auto selection of the best strategies

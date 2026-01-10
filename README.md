# Movie Pipeline

*A set of tools to automate movie library maintenance.*

**⚠️ WARNING: This program is distributed WITHOUT ANY WARRANTY. Use at your own risk.**

## Usage

Run the following command to see available options:

```sh
python app.py --help
```

**Available commands:**

- `archive_movies` – Archive movies based on settings in the config file.
- `detect_segments` – Run best-effort segment detection.

- `process_movie` – Cut and merge movie segments to retain only relevant parts.

### Running Locally

1. Install **Poetry** (if not already installed).

2. Build and install the package:

   ```sh
   poetry build -f wheel
   pip install --user ./dist/movie_pipeline-${VERSION}-py3-none-any.whl
   ```

3. After installation, the following commands will be available:

    | Command | Description |
    |---|---|
    | `movie_pipeline` | Main app (run `movie_pipeline --help` for options) |
    | `movie_pipeline_job_archive_movies` | Executable for the ArchiveMovies xyOps plugin |
    | `movie_pipeline_job_detect_segments` | Executable for the DetectSegments xyOps plugin |
    | `movie_pipeline_job_process_movie` | Executable for the ProcessMovie xyOps plugin (used by ProcessMovieDirectory) |
    | `movie_pipeline_job_process_directory` | Executable for the ProcessMovieDirectory xyOps plugin |

    > **Note:** To use `movie_pipeline_job_process_directory`, you must have a valid API key with **"Edit events"** and **"Run events"** permissions.

### Running with Docker

1. **Build the xyOps Satellite (xySat) integration:**

   ```sh
   docker build --build-context movie_pipeline=. -t fripiane/movie_pipeline_xysat:${VERSION} ./movie_pipeline/jobs/
   ```

2. **Configure `.env`:**

   ```env
   PATHS_INPUT_FOLDER=/mnt/share/video/PVR

   PATHS_MOVIES_FOLDER=/mnt/share/video/PVR/Films
   PATHS_SERIES_FOLDER=/mnt/share/video/PVR/Séries
   PATHS_BACKUP_FOLDER=/mnt/share/usbshare1/Dossier personnel/video/PVR/playground

   ARCHIVE_BASE_BACKUP_FOLDER=/mnt/share/usbshare1/Dossier personnel/video
   LOGGER_LOG_FOLDER=/mnt/share/video/PVR/temp/logs

   SEGMENTDETECTION_TEMPLATES_PATH=/mnt/share/video/PVR/autres/scripts/common-ressources/logo

   # Follow https://github.com/pixlcore/xyops/blob/main/docs/servers.md#automated-server-bootstrap to set and get the API KEY
   XYOPS_setup=http://xyops01:5522/api/app/satellite/config?t=API_KEY_HERE
   ```

3. **Run the containers:**

   ```sh
   docker compose up
   ```

### Setting Up xyOps (Task Scheduler)

1. Access your xyOps instance at **[http://localhost:5522](http://localhost:5522)** or at **[https://localhost:5523](https://localhost:5523)**.

2. Import the plugin manifests from:
   **[`./movie_pipeline/jobs/config/xyops-data-export.txt`](https://github.com/GdPaul1234/movie-pipeline/tree/master/movie_pipeline/jobs/config/xyops-data-export.txt)**
   (via **Admin → System → Import Data...**).

3. **Available events:**
   - Archive Movies
   - Detect Segments
   - Process Movie
   - Process Movie Directory

## Configuration

Before running the program, provide a valid config file.

- **Default location:** `~/.movie_pipeline/config.env`

- **Example configs:** Check the [`tests`](https://github.com/GdPaul1234/movie-pipeline/tree/master/tests) directory.

> [!NOTE]
>
> - Relative paths are resolved from the config folder. Older configs **may break**.
> - **Breaking change:** The config format now uses **Pydantic + python-dotenv** for runtime validation.

### Old vs. New Config Format

#### **Old (INI-style):**

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

#### **New (ENV-style):**

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

## Main Commands

### **Basic Workflow: Detect & Trim Segments + Move to Media Library**

1. **Fill in the config file** and register all plugins.

2. **Recommended workflow:**
   - Run `detect_segments` to identify relevant segments.

   - Install and run **[movie-pipeline-segments-validator](https://github.com/GdPaul1234/movie-pipeline-segments-validator)** to review and validate segments.

   - Alternatively, manually edit `.yml` files with:
     - Corrected titles (e.g., `Serie Name S01E02.mp4`).
     - Segment ranges (e.g., `00:31:53.960-01:00:51.520,01:06:54.480-01:31:40.160,01:37:34.480-02:23:05.560,`).

        Don't forget to add the leading comma at the end of the segment ranges!

     - `skip_backup: yes` for large files (>10GB).

3. **Process movies** by running `process_movie` (cuts, trims, converts, and moves files).

> [!WARNING]
>
> - The `backup_policy_executor` **deletes original files** if they are identified as **series**.
> - Ensure your system has a **recycle bin** to recover deleted files.

### **Archive Media**

If `base_path` is running low on space, use:

```sh
archive_movies
```

> [!WARNING]
>
> - This command **assumes** you have **periodic backups** of movies in `${base_backup_path}/PVR/Films`.

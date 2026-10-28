from dataclasses import dataclass


@dataclass(frozen=True)
class MediaDownloadOutcome:
    downloaded_file_paths: tuple[str, ...]
    # WHY: EC-07. yt-dlp skips files that already exist; the UI shows "já baixado" instead of
    # pretending a fresh download happened.
    was_already_downloaded: bool

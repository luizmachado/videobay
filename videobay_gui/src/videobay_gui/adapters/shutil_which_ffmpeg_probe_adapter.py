from collections.abc import Callable


class ShutilWhichFfmpegProbeAdapter:
    def __init__(self, find_executable_on_path: Callable[[str], str | None]) -> None:
        self.find_executable_on_path = find_executable_on_path

    def is_ffmpeg_executable_available(self) -> bool:
        # WHY: checked per download, not once at startup, so installing ffmpeg while the app
        # is open takes effect on the next download (EC-04, EC-05).
        return self.find_executable_on_path("ffmpeg") is not None

from typing import Protocol


class FfmpegAvailabilityProbePort(Protocol):
    def is_ffmpeg_executable_available(self) -> bool: ...

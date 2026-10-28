from videobay_gui.core.videobay_user_settings import OutputDirectoryProblem


class FixedFfmpegAvailabilityProbeFake:
    def __init__(self, is_ffmpeg_available: bool) -> None:
        self.is_ffmpeg_available = is_ffmpeg_available

    def is_ffmpeg_executable_available(self) -> bool:
        return self.is_ffmpeg_available


class ScriptedOutputDirectoryAccessProbeFake:
    """Every directory is fine unless a problem was scripted for it."""

    def __init__(self) -> None:
        self.output_directory_problems_by_path: dict[str, OutputDirectoryProblem] = {}

    def find_output_directory_problem(self, output_directory: str) -> OutputDirectoryProblem | None:
        return self.output_directory_problems_by_path.get(output_directory)

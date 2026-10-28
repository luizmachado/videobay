from typing import Protocol

from videobay_gui.core.videobay_user_settings import OutputDirectoryProblem


class OutputDirectoryAccessProbePort(Protocol):
    def find_output_directory_problem(self, output_directory: str) -> OutputDirectoryProblem | None:
        """None means the directory exists and is writable (EC-06)."""
        ...

# WHY: upstream's pytest config has no testpaths, so its "Core test" job (run from the repo root)
# recurses into videobay_gui/ and fails importing a package it never installs. Our suite only
# runs with videobay_gui/ as rootdir (`make test`), so any other rootdir skips this subtree.
from pathlib import Path

import pytest

VIDEOBAY_GUI_SUBPROJECT_ROOT_DIRECTORY = Path(__file__).resolve().parent


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    if config.rootpath.resolve() == VIDEOBAY_GUI_SUBPROJECT_ROOT_DIRECTORY:
        return None
    return True

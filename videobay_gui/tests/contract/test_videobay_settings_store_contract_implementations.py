from pathlib import Path

import pytest

from tests.contract.videobay_settings_store_port_contract import (
    CONTRACT_DEFAULT_OUTPUT_DIRECTORY,
    VideobaySettingsStorePortContract,
)
from tests.fakes.in_memory_videobay_settings_store_fake import InMemoryVideobaySettingsStoreFake
from videobay_gui.adapters.json_file_videobay_settings_store_adapter import (
    JsonFileVideobaySettingsStoreAdapter,
)
from videobay_gui.ports.videobay_settings_store_port import VideobaySettingsStorePort


class TestInMemoryVideobaySettingsStoreFakeHonoursContract(VideobaySettingsStorePortContract):
    def build_settings_store_under_contract(self) -> VideobaySettingsStorePort:
        return InMemoryVideobaySettingsStoreFake(CONTRACT_DEFAULT_OUTPUT_DIRECTORY)


class TestJsonFileVideobaySettingsStoreAdapterHonoursContract(VideobaySettingsStorePortContract):
    @pytest.fixture(autouse=True)
    def use_temporary_settings_file(self, tmp_path: Path) -> None:
        self.temporary_settings_file = tmp_path / "config" / "videobay" / "settings.json"

    def build_settings_store_under_contract(self) -> VideobaySettingsStorePort:
        return JsonFileVideobaySettingsStoreAdapter(
            self.temporary_settings_file, CONTRACT_DEFAULT_OUTPUT_DIRECTORY
        )

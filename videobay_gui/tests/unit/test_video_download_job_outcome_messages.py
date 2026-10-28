import pytest

from videobay_gui.core.media_download_outcome import MediaDownloadOutcome
from videobay_gui.core.video_download_job_outcome_messages import (
    describe_finished_download_outcome_for_job_row,
)


@pytest.mark.parametrize(
    ("downloaded_file_count", "expected_playlist_item_count", "expected_message"),
    [(3, 3, "3 de 3 baixados"), (2, 5, "2 de 5 baixados"), (0, 4, "0 de 4 baixados")],
)
def test_ec11_playlist_outcome_reports_how_many_items_arrived(
    downloaded_file_count: int, expected_playlist_item_count: int, expected_message: str
):
    media_download_outcome = MediaDownloadOutcome(
        tuple(f"/d/{index}.mp4" for index in range(downloaded_file_count)), False
    )

    assert (
        describe_finished_download_outcome_for_job_row(
            media_download_outcome, expected_playlist_item_count
        )
        == expected_message
    )


def test_single_video_outcome_keeps_showing_the_file_name():
    assert (
        describe_finished_download_outcome_for_job_row(
            MediaDownloadOutcome(("/d/Aula [abc] 720p.mp4",), False), None
        )
        == "Aula [abc] 720p.mp4"
    )

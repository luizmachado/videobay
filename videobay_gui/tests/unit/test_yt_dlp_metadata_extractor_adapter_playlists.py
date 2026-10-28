from tests.unit.test_yt_dlp_metadata_extractor_adapter import build_adapter_with_scripted_client
from videobay_gui.core.inspected_media_summary import InspectedPlaylistEntry

SAMPLE_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PL123"


def test_ec12_maps_flat_playlist_entries_with_one_based_indices():
    adapter, _ = build_adapter_with_scripted_client(
        {
            "_type": "playlist",
            "title": "Curso de Python",
            "channel": "Canal Dev",
            "entries": [
                {"id": "a1", "title": "Aula 1", "duration": 600.4},
                {"id": "a2", "title": "[Private video]", "duration": None},
                {"id": "a3", "title": "[Deleted video]"},
                {"id": "a4"},
                None,
            ],
        }
    )

    playlist_summary = adapter.extract_inspected_media_summary(SAMPLE_PLAYLIST_URL)

    assert playlist_summary.is_inspected_media_a_playlist
    assert playlist_summary.media_title == "Curso de Python"
    assert playlist_summary.media_uploader_name == "Canal Dev"
    assert playlist_summary.inspected_playlist_entries == (
        InspectedPlaylistEntry(1, "Aula 1", 600, True),
        InspectedPlaylistEntry(2, "[Private video]", None, False),
        InspectedPlaylistEntry(3, "[Deleted video]", None, False),
        InspectedPlaylistEntry(4, "Vídeo 4", None, True),
        InspectedPlaylistEntry(5, "Vídeo 5", None, False),
    )


def test_single_video_has_no_playlist_entries():
    adapter, _ = build_adapter_with_scripted_client({"title": "x", "_type": "video"})

    assert (
        adapter.extract_inspected_media_summary(SAMPLE_PLAYLIST_URL).inspected_playlist_entries
        == ()
    )

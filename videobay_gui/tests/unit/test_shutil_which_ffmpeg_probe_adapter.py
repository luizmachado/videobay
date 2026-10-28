from videobay_gui.adapters.shutil_which_ffmpeg_probe_adapter import ShutilWhichFfmpegProbeAdapter


def test_reports_ffmpeg_available_when_found_on_path():
    assert ShutilWhichFfmpegProbeAdapter(
        lambda _name: "/usr/bin/ffmpeg"
    ).is_ffmpeg_executable_available()


def test_reports_ffmpeg_missing_when_not_on_path():
    assert not ShutilWhichFfmpegProbeAdapter(lambda _name: None).is_ffmpeg_executable_available()

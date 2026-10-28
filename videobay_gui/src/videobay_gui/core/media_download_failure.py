from enum import StrEnum


class MediaDownloadFailureKind(StrEnum):
    NETWORK_UNREACHABLE = "network_unreachable"
    MEDIA_UNAVAILABLE = "media_unavailable"
    OUTPUT_DISK_FULL = "output_disk_full"
    OUTPUT_DIRECTORY_NOT_WRITABLE = "output_directory_not_writable"
    POSTPROCESSING_FAILED = "postprocessing_failed"
    BROKEN_SITE_EXTRACTOR = "broken_site_extractor"
    UNKNOWN_DOWNLOAD_FAILURE = "unknown_download_failure"


class MediaDownloadFailedError(Exception):
    def __init__(
        self, media_download_failure_kind: MediaDownloadFailureKind, technical_detail: str
    ) -> None:
        super().__init__(technical_detail)
        self.media_download_failure_kind = media_download_failure_kind


class MediaDownloadCancelledError(Exception):
    """Raised by executors when the cancellation check returned True (EC-09)."""


MEDIA_DOWNLOAD_FAILURE_MESSAGES_FOR_USER = {
    MediaDownloadFailureKind.NETWORK_UNREACHABLE: (
        "A conexão caiu durante o download. Tente de novo; o download continua de onde parou."
    ),
    MediaDownloadFailureKind.MEDIA_UNAVAILABLE: (
        "O site recusou o download: o vídeo pode ter ficado indisponível ou exigir login."
    ),
    MediaDownloadFailureKind.OUTPUT_DISK_FULL: (
        "Sem espaço no disco. Libere espaço e tente de novo."
    ),
    MediaDownloadFailureKind.OUTPUT_DIRECTORY_NOT_WRITABLE: (
        "Sem permissão para gravar na pasta de destino. Escolha outra pasta."
    ),
    MediaDownloadFailureKind.POSTPROCESSING_FAILED: (
        "O download terminou, mas o ffmpeg falhou ao juntar ou converter o arquivo."
    ),
    # PROVENANCE: EC-18, same meaning as MediaInspectionFailureKind.BROKEN_SITE_EXTRACTOR.
    MediaDownloadFailureKind.BROKEN_SITE_EXTRACTOR: (
        "O site mudou e esta versão do yt-dlp ainda não sabe lê-lo. Sincronize o fork com o "
        "yt-dlp original (git merge upstream/master) para receber a correção."
    ),
    MediaDownloadFailureKind.UNKNOWN_DOWNLOAD_FAILURE: "O download falhou. Tente de novo.",
}

# WHY: disk-full is retryable because the user can free space and resume the .part file;
# a permission or ffmpeg failure would just fail the same way again.
RETRYABLE_MEDIA_DOWNLOAD_FAILURE_KINDS = frozenset(
    {
        MediaDownloadFailureKind.NETWORK_UNREACHABLE,
        MediaDownloadFailureKind.OUTPUT_DISK_FULL,
        MediaDownloadFailureKind.UNKNOWN_DOWNLOAD_FAILURE,
    }
)


def describe_media_download_failure_for_user(
    media_download_failure_kind: MediaDownloadFailureKind,
) -> str:
    return MEDIA_DOWNLOAD_FAILURE_MESSAGES_FOR_USER[media_download_failure_kind]


def is_media_download_failure_retryable(
    media_download_failure_kind: MediaDownloadFailureKind,
) -> bool:
    return media_download_failure_kind in RETRYABLE_MEDIA_DOWNLOAD_FAILURE_KINDS

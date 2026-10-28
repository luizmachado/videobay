from enum import StrEnum


class MediaInspectionFailureKind(StrEnum):
    UNSUPPORTED_SITE = "unsupported_site"
    MEDIA_UNAVAILABLE = "media_unavailable"
    GEO_RESTRICTED = "geo_restricted"
    AGE_RESTRICTED = "age_restricted"
    NETWORK_UNREACHABLE = "network_unreachable"
    LIVE_BROADCAST_NOT_SUPPORTED = "live_broadcast_not_supported"
    BROKEN_SITE_EXTRACTOR = "broken_site_extractor"
    UNKNOWN_EXTRACTION_FAILURE = "unknown_extraction_failure"


class MediaInspectionFailedError(Exception):
    def __init__(
        self, media_inspection_failure_kind: MediaInspectionFailureKind, technical_detail: str
    ) -> None:
        super().__init__(technical_detail)
        self.media_inspection_failure_kind = media_inspection_failure_kind


MEDIA_INSPECTION_FAILURE_MESSAGES_FOR_USER = {
    MediaInspectionFailureKind.UNSUPPORTED_SITE: "Este site não é suportado pelo yt-dlp.",
    MediaInspectionFailureKind.MEDIA_UNAVAILABLE: (
        "Vídeo indisponível: pode ser privado, ter sido removido ou exigir login."
    ),
    MediaInspectionFailureKind.GEO_RESTRICTED: "Este vídeo está bloqueado na sua região.",
    MediaInspectionFailureKind.AGE_RESTRICTED: (
        "Este vídeo tem restrição de idade e exige login, o que ainda não é suportado."
    ),
    MediaInspectionFailureKind.NETWORK_UNREACHABLE: (
        "Sem conexão com o site. Verifique a internet e tente de novo."
    ),
    MediaInspectionFailureKind.LIVE_BROADCAST_NOT_SUPPORTED: (
        "Transmissões ao vivo não são suportadas nesta versão."
    ),
    # PROVENANCE: EC-18. yt-dlp marks these as bugs ("please report this issue"); fixes land
    # upstream, so the action is syncing the fork, not retrying.
    MediaInspectionFailureKind.BROKEN_SITE_EXTRACTOR: (
        "O site mudou e esta versão do yt-dlp ainda não sabe lê-lo. Sincronize o fork com o "
        "yt-dlp original (git merge upstream/master) para receber a correção."
    ),
    MediaInspectionFailureKind.UNKNOWN_EXTRACTION_FAILURE: (
        "Não foi possível ler este endereço. Tente de novo."
    ),
}

# WHY: only failures that may succeed on a second attempt offer "tentar de novo" (EC-03);
# offering retry for a private or geo-blocked video would just repeat the same error.
RETRYABLE_MEDIA_INSPECTION_FAILURE_KINDS = frozenset(
    {
        MediaInspectionFailureKind.NETWORK_UNREACHABLE,
        MediaInspectionFailureKind.UNKNOWN_EXTRACTION_FAILURE,
    }
)


def describe_media_inspection_failure_for_user(
    media_inspection_failure_kind: MediaInspectionFailureKind,
) -> str:
    return MEDIA_INSPECTION_FAILURE_MESSAGES_FOR_USER[media_inspection_failure_kind]


def is_media_inspection_failure_retryable(
    media_inspection_failure_kind: MediaInspectionFailureKind,
) -> bool:
    return media_inspection_failure_kind in RETRYABLE_MEDIA_INSPECTION_FAILURE_KINDS

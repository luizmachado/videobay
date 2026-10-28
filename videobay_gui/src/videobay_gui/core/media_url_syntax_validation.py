from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlsplit

# WHY: yt-dlp also accepts file:// and other schemes, but the GUI only targets web media
# (ARCHITECTURE.md, EC-01); local files would bypass the destination-folder checks.
ACCEPTED_MEDIA_URL_SCHEMES = frozenset({"http", "https"})


class MediaUrlRejectionReason(StrEnum):
    EMPTY_MEDIA_URL = "empty_media_url"
    MISSING_URL_SCHEME = "missing_url_scheme"
    UNSUPPORTED_URL_SCHEME = "unsupported_url_scheme"
    MISSING_URL_HOST = "missing_url_host"
    WHITESPACE_INSIDE_URL = "whitespace_inside_url"


@dataclass(frozen=True)
class MediaUrlSyntaxValidationOutcome:
    normalized_media_url: str
    media_url_rejection_reason: MediaUrlRejectionReason | None

    @property
    def is_media_url_acceptable(self) -> bool:
        return self.media_url_rejection_reason is None


MEDIA_URL_REJECTION_MESSAGES_FOR_USER = {
    MediaUrlRejectionReason.EMPTY_MEDIA_URL: "Cole o endereço de um vídeo ou playlist.",
    MediaUrlRejectionReason.MISSING_URL_SCHEME: "O endereço precisa começar com http:// ou https://.",
    MediaUrlRejectionReason.UNSUPPORTED_URL_SCHEME: "Só endereços http:// ou https:// são aceitos.",
    MediaUrlRejectionReason.MISSING_URL_HOST: "O endereço não tem um site (ex.: youtube.com).",
    MediaUrlRejectionReason.WHITESPACE_INSIDE_URL: "O endereço não pode ter espaços no meio.",
}


def validate_media_url_syntax(raw_media_url: str) -> MediaUrlSyntaxValidationOutcome:
    normalized_media_url = raw_media_url.strip()
    media_url_rejection_reason = find_media_url_rejection_reason(normalized_media_url)
    return MediaUrlSyntaxValidationOutcome(normalized_media_url, media_url_rejection_reason)


def find_media_url_rejection_reason(normalized_media_url: str) -> MediaUrlRejectionReason | None:
    if not normalized_media_url:
        return MediaUrlRejectionReason.EMPTY_MEDIA_URL
    if any(media_url_character.isspace() for media_url_character in normalized_media_url):
        return MediaUrlRejectionReason.WHITESPACE_INSIDE_URL
    if "://" not in normalized_media_url:
        return MediaUrlRejectionReason.MISSING_URL_SCHEME
    split_media_url = urlsplit(normalized_media_url)
    if split_media_url.scheme.lower() not in ACCEPTED_MEDIA_URL_SCHEMES:
        return MediaUrlRejectionReason.UNSUPPORTED_URL_SCHEME
    if not split_media_url.hostname:
        return MediaUrlRejectionReason.MISSING_URL_HOST
    return None


def describe_media_url_rejection_reason_for_user(
    media_url_rejection_reason: MediaUrlRejectionReason,
) -> str:
    return MEDIA_URL_REJECTION_MESSAGES_FOR_USER[media_url_rejection_reason]

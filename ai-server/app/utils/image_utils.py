import base64
import binascii
import re


DATA_IMAGE_PATTERN = re.compile(r"^data:image/[a-zA-Z0-9.+-]+;base64,(?P<data>.+)$", re.DOTALL)


def is_valid_base64_image(value: str) -> bool:
    if not value:
        return False

    match = DATA_IMAGE_PATTERN.match(value)
    if not match:
        return False

    try:
        decoded = base64.b64decode(match.group("data"), validate=True)
    except (binascii.Error, ValueError):
        return False

    return (
        decoded.startswith(b"\x89PNG\r\n\x1a\n")
        or decoded.startswith(b"\xff\xd8\xff")
        or decoded.startswith(b"GIF87a")
        or decoded.startswith(b"GIF89a")
        or (len(decoded) >= 12 and decoded[:4] == b"RIFF" and decoded[8:12] == b"WEBP")
    )

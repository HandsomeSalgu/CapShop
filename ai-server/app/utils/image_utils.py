def is_valid_base64_image(value: str) -> bool:
    if not value:
        return False

    return value.startswith("data:image/")

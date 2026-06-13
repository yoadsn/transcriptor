from app.config import settings

LOCAL_IMAGES_SERVE_ROOT_PATH = "images"


def resolve_image_url(image_path: str) -> str:
    """Resolve a stored image_path to a public URL. Swap this for object storage."""

    # When the images are already stored at a remote
    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path

    # When the app is configured with a specific image origin remote
    if settings.images_serve_origin:
        return f"{settings.images_serve_origin}/{image_path}"

    # Local serving
    return f"/{LOCAL_IMAGES_SERVE_ROOT_PATH}/{image_path}"

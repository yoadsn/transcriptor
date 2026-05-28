def resolve_image_url(image_path: str) -> str:
    """Resolve a stored image_path to a public URL. Swap this for object storage."""
    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path
    return f"/images/{image_path}"

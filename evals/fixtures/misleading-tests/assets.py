from pathlib import Path


def resolve_asset(root, requested):
    root = Path(root).resolve()
    target = (root / requested).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError("outside assets")
    return target

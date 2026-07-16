from __future__ import annotations

import os


def is_production() -> bool:
    return os.environ.get("HOUSEFLAVOR_ENV", "development").lower() == "production"

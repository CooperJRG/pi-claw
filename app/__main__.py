"""Allow running the display app as `python -m app` from the repo root."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure `openclaw_display` is importable when run as `python -m app`
_app_dir = Path(__file__).resolve().parent
if str(_app_dir) not in sys.path:
    sys.path.insert(0, str(_app_dir))

from openclaw_display.main import main

if __name__ == "__main__":
    raise SystemExit(main())

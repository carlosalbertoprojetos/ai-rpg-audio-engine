"""Pytest bootstrap for local import isolation."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

existing_app = sys.modules.get("app")
if existing_app is not None:
    module_file = getattr(existing_app, "__file__", "")
    if module_file and str(ROOT) not in module_file:
        to_delete = [name for name in sys.modules if name == "app" or name.startswith("app.")]
        for name in to_delete:
            del sys.modules[name]

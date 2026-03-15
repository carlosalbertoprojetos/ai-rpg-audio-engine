from __future__ import annotations

import pcbagent.generated.api.system as generated_module


def test_system_module_is_importable() -> None:
    assert generated_module is not None

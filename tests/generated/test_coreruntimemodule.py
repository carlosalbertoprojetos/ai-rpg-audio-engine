from __future__ import annotations

import pcbagent.generated.core_runtime.coreruntimemodule as generated_module


def test_coreruntimemodule_module_is_importable() -> None:
    assert generated_module is not None

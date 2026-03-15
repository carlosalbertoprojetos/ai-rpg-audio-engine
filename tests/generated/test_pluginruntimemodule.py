from __future__ import annotations

import pcbagent.generated.plugin_runtime.pluginruntimemodule as generated_module


def test_pluginruntimemodule_module_is_importable() -> None:
    assert generated_module is not None

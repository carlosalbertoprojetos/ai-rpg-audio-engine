from __future__ import annotations

from pcbagent.generated.plugin_runtime.pluginruntimemodule import PluginRuntimeModule


def test_plugin_runtime_starter_class_executes() -> None:
    instance = PluginRuntimeModule()
    result = instance.execute()

    assert result["module"] == "plugin_runtime"
    assert result["class"] == "PluginRuntimeModule"
    assert result["status"] == "ready"

from backend.models.audio_request import SceneLayer
from backend.orchestration.provider_selector import ProviderSelector


def _layer(sound_type: str) -> SceneLayer:
    return SceneLayer(
        layer_id="l1",
        label="test",
        sound_type=sound_type,
        intensity=0.7,
        volume=0.6,
        duration_seconds=10.0,
        distance="mid",
        environment="outdoor",
    )


def test_provider_selector_rules() -> None:
    selector = ProviderSelector()

    assert selector.select(_layer("environment"))[0] == "freesound"
    assert selector.select(_layer("cinematic_music"))[0] == "aiva"
    assert selector.select(_layer("dynamic_music"))[0] == "mubert"
    assert selector.select(_layer("commercial_asset"))[0] == "shutterstock"

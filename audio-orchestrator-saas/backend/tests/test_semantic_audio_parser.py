from backend.services.semantic_audio_parser import SemanticAudioParser


def test_semantic_parser_extracts_expected_dimensions() -> None:
    parser = SemanticAudioParser()
    profile = parser.parse("people whispering close in dark corridor")

    assert profile.sound_type == "human_voice"
    assert profile.distance == "near"
    assert profile.environment == "indoor"
    assert profile.emotion == "tense"
    assert 0.1 <= profile.intensity <= 1.0

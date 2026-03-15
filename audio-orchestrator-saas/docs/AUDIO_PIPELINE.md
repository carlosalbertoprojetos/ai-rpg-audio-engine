# AUDIO PIPELINE

## Flow

User Request
-> Semantic Analysis
-> Scene Decomposition
-> Provider Selection
-> Audio Retrieval/Generation
-> Layer Composition
-> Mixing
-> Export

## Runtime details

1. `SemanticAudioParser` extracts emotion, intensity, environment, distance, era, and sound type.
2. `AudioLayerEngine` creates up to `max_layers` scene layers with per-layer volume.
3. `ProviderSelector` chooses provider order based on sound type with fallback chain.
4. Providers return one candidate `AudioAsset` per layer.
5. `LicensingValidator` blocks non-commercial-safe licenses.
6. `AudioMixer` synthesizes and mixes layers, exporting `wav` directly and `mp3/ogg` via ffmpeg.
7. Metadata is persisted to SQLite and cached in Redis (or in-memory fallback).

## Caching

Cache key = `sha256(json.dumps(request_parameters, sort_keys=True))`

Cached response includes scene metadata and layer/provider results.

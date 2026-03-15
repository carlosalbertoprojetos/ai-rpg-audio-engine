# AGENTS.md

## Operating rules for coding agents

1. Inspect existing files before editing.
2. Reuse modules; do not duplicate domain logic.
3. Keep orchestration flow centralized in `backend/orchestration/audio_pipeline.py`.
4. Add tests for parser, provider selection, API routes, and caching behavior.
5. Preserve license safety checks for all provider assets.
6. For new providers, implement `BaseAudioProvider` and register in `AudioPipeline.providers`.
7. Update `docs/AUDIO_PIPELINE.md` and `docs/PROVIDER_INTEGRATION.md` when changing behavior.

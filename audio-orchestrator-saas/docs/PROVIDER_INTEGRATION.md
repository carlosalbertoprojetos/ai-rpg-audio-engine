# PROVIDER INTEGRATION

## Supported providers

- Freesound
- Epidemic Sound
- Artlist
- Shutterstock Audio
- Adobe Stock (via commercial stock adapter)
- AIVA
- Mubert

## Integration model

Each provider implements `BaseAudioProvider.fetch_asset(layer, context)` and returns:

- `asset_id`
- `provider`
- `title`
- `source_url`
- `license_type`
- `duration_seconds`
- `layer_id`

## Selection logic

- `environment` -> Freesound (fallback Epidemic, Artlist)
- `cinematic_music` -> AIVA (fallback Artlist, Epidemic)
- `dynamic_music` -> Mubert (fallback AIVA, Artlist)
- `commercial_asset` -> Shutterstock/Adobe (fallback Artlist)

## License safety

Allowed:
- `royalty_free`
- `commercial_safe`
- `cc0`
- `cc_by`
- `standard_commercial`

Denied:
- `cc_by_nc`
- `cc_by_nc_sa`
- `editorial_only`
- `personal_use_only`
- `unknown`

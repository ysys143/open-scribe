# Changelog

## 0.3.0 — 2026-11-07

### Added

- `openscribe`, `scribe`, and `scr` entrypoints; `ls [n]` lists recent recordings (default 10).
- Configured hosted ASR and text models, with Scribe v2 and GPT-6 Luna defaults.
- Summary-model speaker-name inference only for actual diarization output, within the existing summary request.
- Request-scoped speaker labels, validated self-introduction evidence, raw transcript preservation, and name-only replacement.
- `config show` and `config validate`; explicit credential-file references with owner-only permissions.

### Changed

- General settings use one `settings.json` document. Ordinary `.env` files and legacy option environment variables are no longer loaded.
- Copy destinations use `copy_to_path`; null disables copying. Existing CLI flags override JSON for one invocation.
- Restored title-based transcript/summary filenames, transcript display, and copies, preserving the 0.2.4 CLI workflow.
- Internal config/providers/speech/postprocess/presentation/runtime and integration modules are separated.
- Research reports remain in `docs/research`; superseded designs and documentation are archived.

### Fixed

- Local input audio is preserved during temporary-file cleanup.
- Homebrew installation no longer creates credential files, exports their contents, or updates dependencies on invocation.

### Upgrade notes

General settings must be moved from old `.env` variables into `~/.config/open-scribe/settings.json`.
Use `settings.example.json` as a starting point without overwriting an existing settings file.
Set `copy_to_path` explicitly to keep copies enabled. Reference existing key files with
`providers.<provider>.api_key_file` and `api_key_env`; never put key values in JSON.
The default Scribe v2 route needs an OpenRouter credential. Older engines remain selectable with `--engine`.
`OPEN_SCRIBE_SETTINGS` selects another JSON document. `--update-key` now displays guidance only.

Verification uses isolated files/databases and mocked provider responses. No paid ASR/LLM calls or live
Notion/Telegram publication are part of the release check; model availability is checked through public metadata.

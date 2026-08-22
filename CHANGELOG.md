# Changelog

All notable changes to this project are documented here. The format loosely
follows [Keep a Changelog](https://keepachangelog.com/), and the project uses
[Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-08-22

First stable release.

### Added
- Natural-language control of OBS Studio via **Claude** or **ChatGPT** (bring
  your own API key), using LLM tool-calling over obs-websocket v5.
- Tool coverage: audio filters (noise suppression, gate, compressor, EQ, gain),
  volume/mute, video resolution & fps, scenes/sources, and opt-in
  streaming/recording (service, encoder/bitrate, start/stop).
- **Professional studio UI**: an ivory canvas with warm-ink text and a single
  deep-teal accent, full-bleed dark banners at the top (masthead) and bottom
  (footer), clickable starting-point prompts, styled action-step cards, a
  connection status pill, and a copyright footer. Type is shared with the
  project writeup (Fraunces / Hanken Grotesk / JetBrains Mono).
- Ivory base theme pinned via `.streamlit/config.toml`.
- Project header image, architecture diagram, and a Medium-style writeup.

### Notes
- Streaming/recording tools are disabled by default and gated behind a sidebar
  toggle, since they can start a public broadcast or change the stream key.
- API keys and the OBS password are held only in the running session and are
  never written to disk by the app.

# MiniMax Voice Notes

- TTS endpoint (HTTP): `POST https://api.minimax.io/v1/t2a_v2`
- Alternative region endpoint: `POST https://api-uw.minimax.io/v1/t2a_v2`
- Auth header: `Authorization: Bearer <MINMAX_API_KEY>`

Voice list:

- Check MiniMax official voice list docs:
  - https://www.minimax.io/platform/document/T2A%20V2?key=67ac78f2096ecadac29f4ca3
  - https://www.minimax.io/platform/document/Voice%20cloning?key=677f1474f8ecca8b19710d20

Notes:

- Some voice IDs are system preset voices.
- Some voice IDs are account-specific (for cloned/custom voices).
- Keep `voice_id` configurable at runtime; do not hardcode a single voice.

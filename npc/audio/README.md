# Heraldor audio catalog

Only clip IDs declared in `clips.json` may reach the Discord voice relay. Story
events contain an ID, never a filename, URL, channel or FFmpeg argument. The
relay verifies the final asset's SHA-256 before it logs in.

`servants_after_three_v1.ogg` was rendered from the operator-supplied
`horror_raw.mp3` as 48 kHz stereo Opus. Its internal dramatic pauses were kept;
the level was moved only slightly to the Discord-oriented -16 LUFS target.

For another clip, keep the original outside the runtime image, render one final
48 kHz Opus/Ogg delivery asset, inspect duration and loudness, then add a new
fixed ID plus the delivery file's hash here. Never accept a path or URL from an
event payload.

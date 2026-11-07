---
name: project-ffmpeg-btbn-master-aac-hang
description: "twitter-snap-api nvenc stall of Nov 2026 was FFmpeg master's aac encoder (nmr coder) looping on some 48 kHz audio, not nvenc; BtbN release builds work; repro files in tools/out/nvenc_repro"
metadata:
  type: project
---

The twitter-snap-api "nvenc hang" of 2026-11-06/07 (private_bot `HeadersTimeoutError` after 300 s, every later request queued
behind the mutex) was the **aac encoder of the BtbN `ffmpeg-master-latest` build** (N-128560, 2026-11-07) that `build.sh` downloaded:
its default `nmr` coder loops forever on some 48 kHz stereo audio (post 2111792834483556435; a 2 s float WAV of it reproduces,
`tools/out/nvenc_repro/hang_2s_f32_u.wav`; `-aac_coder twoloop` / `fast` and `-ar 44100` do not hang). The stuck ffmpeg sits at
`frame=0`, ignores SIGTERM (needs KILL), and hevc_nvenc / tpad / alphamerge were never the problem. Ubuntu 6.1.1, BtbN n8.1 and
n9.0 encode the same line in 33 s on the sandbox's RTX 3080 Ti. Fix: twitter-snap-api #22 pins `build.sh` to the n9.0 release line.

**Why:** a nightly master ffmpeg in a production image turned an upstream encoder regression into a stuck service; the symptom
(only some posts hang, health check fine) hid the real cause for a week.
**How to apply:** when a render "hangs", bisect the logged ffmpeg line by stage (audio-only, video-only, filter by filter) with
`timeout -s KILL`, and compare builds before suspecting the GPU. Downloaded BtbN builds live in `tools/out/ffmpeg-{btbn,n81,n90}`.
See [[project-twitter-snap-dev-facts]].

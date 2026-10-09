---
name: reel-craft-engine
description: >-
  Autonomous AI Video & Reel Motion Graphics Engine. Turns raw audio, video clips, or scripts into
  production-grade viral vertical reels (1080x1920, 9:16). Transcribes speech with millisecond word sync,
  designs dynamic storyboards with 3D Fluent icons, macOS code cards, status badges, and SFX,
  and renders high-retention motion graphics with adjustable pacing (ultra-fast, fast-viral, cinematic).
---

# Reel Craft Engine: Autonomous Short-Form Video & Motion Graphics Production

Reel Craft Engine is a complete, multi-agent skill for generating high-retention vertical reels, TikToks, and YouTube Shorts from scratch or editing existing video footage.

---

## 1. When to Trigger This Skill

Trigger `reel-craft-engine` whenever the user asks to:
1. **Turn Audio into a Reel**: User provides voiceover (`.mp3`, `.wav`) and wants an engaging motion graphics video without needing a video editor.
2. **Edit & Enhance Existing Video**: User provides raw video (`.mp4`, `.mov`) and wants auto-subtitles with millisecond sync, dynamic zoom punches, B-roll overlays, and SFX.
3. **Generate Tech / SaaS Product Showcases**: User wants to display macOS code editors, 3D animated tech icons, live UI mockups, split comparisons, and glowing kinetic typography.
4. **Accelerate or Change Video Pacing**: Speed up speech cuts, apply TikTok-style rapid cuts, or build smooth Apple-keynote style motion.

---

## 2. Core Architecture & Workflow

```
+-----------------------------------+
|  1. INGEST & TRANSCRIBE           | --> Runs Whisper with word-level millisecond timestamps.
|  transcribe.py                    |     Detects pauses, speech cadence, and WPM rate.
+-----------------------------------+
                  |
                  v
+-----------------------------------+
|  2. STORYBOARD & MOTION DESIGN   | --> Maps speech semantics to 3D icons, code cards, and UI widgets.
|  synthesize_storyboard.py         |     Applies Pacing Preset (ultra_fast / fast_viral / cinematic_tech).
+-----------------------------------+     Generates comprehensive project.json.
                  |
                  v
+-----------------------------------+
|  3. SYNCHRONIZE & SOUND DESIGN    | --> Injects audio hook booster (+4dB to +5dB for first 3s).
|  audio.py & SFX Library           |     Aligns whooshes, glitches, sub-bass hits, and pops to key frames.
+-----------------------------------+
                  |
                  v
+-----------------------------------+
|  4. HIGH-SPEED MULTITHREAD RENDER | --> Renders 1080x1920 60fps/30fps video via ReelRenderer.
|  render_cli.py                    |     Assembles final master video with AAC audio stream.
+-----------------------------------+
```

---

## 3. Pacing Presets

The agent must select the pacing preset that matches the target audience:

1. **`ultra_fast`** (Gen-Z / TikTok Shock Pace):
   - Fast 0.2s - 0.35s word cuts.
   - 3 to 6 words maximum per scene card.
   - Aggressive punch-in zooms on power words.
   - Glitch and fast whoosh SFX every 1.5 seconds.
2. **`fast_viral`** (Instagram Reels / YouTube Shorts Standard - **Default**):
   - 3.0s - 4.5s scene pacing.
   - Dual-tone active word karaoke glowing typography (`#B7EC03` on white).
   - Dynamic 3D Fluent icons with spring bounce interpolation.
   - Clean sub-bass hook at second 0.00.
3. **`cinematic_tech`** (Developer / B2B SaaS Keynote):
   - 5.0s - 8.0s scene pacing.
   - Detailed macOS code editor typing (`code_card`).
   - Steady ambient tech glow and subtle foreground parallax.
   - Zero background flicker (rock-solid cyber grid).

---

## 4. Execution Protocol for Agents

When invoked with an audio or video path:

### Step 1: Transcribe & Extract Word Timings
Run the built-in transcription script:
```bash
python3 /home/omar/.gemini/config/skills/reel-craft-engine/scripts/transcribe.py \
  "<INPUT_AUDIO_OR_VIDEO_PATH>" \
  --output "transcript.json" \
  --model base \
  --lang ar
```

### Step 2: Generate or Customize `project.json`
Run the synthesizer to scaffold the storyboard:
```bash
python3 /home/omar/.gemini/config/skills/reel-craft-engine/scripts/synthesize_storyboard.py \
  "transcript.json" \
  --audio "<VOICEOVER_PATH>" \
  --output "project.json" \
  --pacing fast_viral \
  --name "Reel Title"
```

*Agent Note*: Inspect `project.json` and customize hero visual elements:
- Use `type: "icon"` for key concepts (browse available 3D icons in `assets/icons_3d/`).
- Use `type: "code_card"` when discussing programming, APIs, or database queries.
- Use `type: "badge"` for performance numbers (e.g. `100% بدون تهنيج`).
- Use `type: "video_loop"` or image mockups for actual screenshots.

### Step 3: Render Master Video
Render the finalized vertical reel:
```bash
python3 /home/omar/.gemini/config/skills/reel-craft-engine/scripts/render_cli.py \
  "project.json" \
  --output "output/final_reel.mp4" \
  --threads 8
```

---

## 5. Visual Asset Library

- **3D Icons**: Located at `assets/icons_3d/` (19+ high-resolution 3D Fluent icons):
  - `zap.png` (Speed / Fast)
  - `keyboard.png` (Keyboard / Typing)
  - `hardware.png` / `cpu.png` (Hardware / Legacy Devices)
  - `monitor.png` / `mobile.png` (Screens & Interfaces)
  - `cloud.png` (Cloud Infrastructure)
  - `lock.png` / `shield.png` (Security & Protection)
  - `chart.png` / `cart.png` / `receipt.png` (Sales / Retail / POS)
  - `code.png` / `bulb.png` / `rocket.png` / `fire.png` (Innovation / Tech)
- **Sound Effects**: Located at `assets/sfx/`:
  - `Hit.mp3` (Sub-bass impact hook)
  - `whoosh-blow-flutter-shortwav-14678.mp3` / `Air Whoosh 02.wav` (Scene transitions)
  - `mixkit-small-sci-fi-glitch-1030.wav` (Error / Glitch reveals)
  - `cashier-quotka-chingquot-sound-effect-129698.mp3` (Financial & Speed achievements)
  - `pop.mp3` (Icon pop bounce)
- **Fonts**: Located at `assets/fonts/`:
  - `IBMPlexSansArabic-Bold.ttf`, `Alexandria-Bold.ttf`, `Cairo-Black.ttf`, `FiraCode-Medium.ttf`.

---

## 6. Multi-Agent Portability (Antigravity, Claude Code, Codex, Cursor)

This skill is installed system-wide in `~/.gemini/config/skills/reel-craft-engine/` and duplicated in workspace `skills/reel-craft-engine/`.
Any coding agent can read this `SKILL.md` to autonomously plan, storyboard, and render studio-grade reels without user intervention.

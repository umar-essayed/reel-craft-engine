# 🎬 Reel Craft Engine (`reel-craft-engine`)
### Autonomous AI Video & Reel Motion Graphics Engine for Coding Agents
> **Turn raw voiceovers, scripts, or video clips into viral 9:16 high-retention vertical reels in minutes.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-green.svg)]()
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)]()
[![AI Agents Supported](https://img.shields.io/badge/Agents-Antigravity%20%7C%20Claude%20Code%20%7C%20Codex%20%7C%20Cursor-purple.svg)]()

---

## ⚡ What is Reel Craft Engine?

**Reel Craft Engine** is an enterprise-grade AI Skill specifically designed for **AI Coding Agents** (Google Antigravity, Claude Code, OpenAI Codex, Cursor). 

It empowers agents to act as **autonomous motion graphics directors and video editors**:
1. **Audio-Only Mode**: Feed it an `.mp3` or `.wav` voiceover. It runs Whisper speech-to-text with millisecond word sync, designs a full storyboard, populates it with 3D Fluent icons, animated macOS code cards, status badges, and SFX, and outputs a 1080x1920 60fps/30fps vertical video.
2. **Video Enhancement Mode**: Feed it raw camera or screen recordings. It cuts dead silences, applies dynamic zoom punches, generates dual-tone glowing subtitles, and layers sound effects.
3. **Pacing Engine**: Supports configurable pacing modes ranging from **`ultra_fast`** (TikTok Gen-Z pace) to **`fast_viral`** (Instagram Reels) and **`cinematic_tech`** (Apple keynote style).

---

## 🚀 Quick Install (1-Line Command)

### Universal One-Liner (Linux & macOS)
```bash
curl -fsSL https://raw.githubusercontent.com/umar-essayed/reel-craft-engine/main/install.sh | bash
```

### Or Clone & Run Manually:
```bash
git clone https://github.com/umar-essayed/reel-craft-engine.git
cd reel-craft-engine
chmod +x install.sh
./install.sh
```

---

## 🤖 How to Use with AI Agents

Once installed, your coding agent gains the ability to create and edit reels directly from your prompt.

### 1. Google Antigravity CLI (`agy`)
Simply mention the skill in your prompt:
```text
Use reel-craft-engine to transcribe /path/to/voiceover.mp3, apply ultra_fast pacing, and render a complete viral reel.
```
*Antigravity automatically discovers the skill in `~/.gemini/config/skills/reel-craft-engine/SKILL.md`.*

### 2. Claude Code (`claude`)
```text
I have a recording at voiceover.wav. Use the reel-craft-engine skill to build a SaaS promo reel with macOS code cards and 3D icons, then export the MP4.
```

### 3. Cursor & Windsurf
Add `reel-craft-engine.md` to `.cursor/rules/` or ask in Cursor Agent mode:
```text
@reel-craft-engine Read project.json and render the reel with 8 threads.
```

### 4. OpenAI Codex / Shell CLI
Run the standalone scripts directly:
```bash
# 1. Transcribe with Whisper (millisecond word sync)
python3 scripts/transcribe.py input_audio.mp3 --output transcript.json --model base --lang ar

# 2. Synthesize Storyboard & Match 3D Assets
python3 scripts/synthesize_storyboard.py transcript.json --audio input_audio.mp3 --pacing fast_viral --output project.json

# 3. High-Speed Multithreaded Render
python3 scripts/render_cli.py project.json --output output/final_reel.mp4 --threads 8
```

---

## 🏎️ Pacing Presets

| Preset | Target Platform | Scene Length | Text Rhythm | SFX Density | Recommended For |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`ultra_fast`** | TikTok, IG Gen-Z | 1.5s - 2.8s | 3-5 words / card, punchy pop | Every 1.0s - 1.5s (Hits, Glitches, Whooshes) | Speed showcases, shock facts, hooks |
| **`fast_viral`** (Default) | Instagram Reels, Shorts | 3.0s - 4.5s | Word-by-word karaoke glow | Every scene transition + key emphasis | SaaS product reels, tips, case studies |
| **`cinematic_tech`** | YouTube, LinkedIn Tech | 5.0s - 8.0s | Multi-line IDE typing | Ambient tech pads, mechanical clicks | In-depth engineering, architecture breakdowns |

---

## 🎨 Asset Ecosystem (Batteries Included)

Reel Craft Engine comes pre-loaded with production assets inside `assets/`:

- **💎 19+ 3D Fluent Icons (`assets/icons_3d/`)**:
  - `zap.png` (Speed / Cloud execution)
  - `keyboard.png` (Keyboard shortcuts & typing)
  - `hardware.png` / `cpu.png` (Legacy devices & hardware specs)
  - `monitor.png` / `mobile.png` (Responsive UI)
  - `cloud.png`, `shield.png`, `lock.png` (Infrastructure & security)
  - `cart.png`, `receipt.png`, `chart.png` (Retail, POS, and sales)
  - `code.png`, `bulb.png`, `fire.png`, `rocket.png` (Development & tech)
- **🔊 SFX Sound Design Library (`assets/sfx/`)**:
  - Sub-bass cinematic hook hits (`Hit.mp3`)
  - Fast air swooshes & directional whooshes (`Air Whoosh 02.wav`, `whoosh_fast.mp3`)
  - Sci-fi error glitches (`mixkit-small-sci-fi-glitch-1030.wav`)
  - Cash register / success chimes (`cashier-quotka-chingquot-sound-effect-129698.mp3`)
  - Pop bounces & mechanical camera clicks (`pop.mp3`, `ES_Camera Shutter Click`)
- **🔤 Typography & Fonts (`assets/fonts/`)**:
  - `IBMPlexSansArabic-Bold.ttf`
  - `Alexandria-Bold.ttf`
  - `Cairo-Black.ttf`
  - `FiraCode-Medium.ttf`

---

## 📐 Project Structure

```
reel-craft-engine/
├── SKILL.md                 # Agent instructions & execution protocol
├── README.md                # Comprehensive documentation & setup
├── install.sh               # 1-click installer for all agent platforms
├── requirements.txt         # Python dependencies
├── scripts/
│   ├── transcribe.py        # Whisper word-level synchronizer
│   ├── synthesize_storyboard.py # Semantic storyboard & widget mapper
│   └── render_cli.py        # Multithreaded 1080x1920 video renderer
├── references/
│   ├── design_system.md     # Motion graphics rules & camera curves
│   └── project_schema.md    # Full project.json JSON schema
├── engine_core/             # High-performance Python rendering engine
│   ├── renderer.py          # Multiprocess frame compositor
│   ├── typography.py        # Bidi Arabic text & karaoke shaper
│   ├── audio.py             # Audio mastering, hook booster & SFX mixer
│   └── config.py            # Resolution, bitrates & presets
└── assets/
    ├── icons_3d/            # 3D Fluent icon pack
    ├── sfx/                 # Curated sound effects
    └── fonts/               # Arabic & Latin typography
```

---

## 🛠️ System Requirements

- **OS**: Linux (Ubuntu/Debian, Arch, Fedora), macOS, or Windows (WSL2 recommended)
- **Python**: 3.10 or higher
- **FFmpeg**: Required (`sudo apt install ffmpeg` or `brew install ffmpeg`)
- **Hardware**: Multi-core CPU (8+ threads recommended for fast rendering)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

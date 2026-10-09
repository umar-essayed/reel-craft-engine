# Design System & Motion Graphics Blueprint

This guide specifies visual rules, pacing standards, color palettes, and motion curves for generating vertical short-form videos (Reels / TikTok / YouTube Shorts) using **Reel Craft Engine**.

---

## 1. Visual Hierarchy & Composition (1080x1920 9:16)

Every frame is layered in strict order:
1. **Background Layer (Z: 0)**:
   - Deep tech dark background (`#0A0A0A` or `#06070B`).
   - Procedural cyber grid (subtle 3-5% opacity), **100% stable / locked camera** to eliminate optical eye strain and flicker.
   - Floating tech embers / glowing particles drifting upward.
2. **Ambient Glow / Backlight (Z: 1)**:
   - Soft radial light behind foreground assets colored with brand accent (`#B7EC03` / `#00E5FF`).
3. **Hero Content / Mockup / Asset Layer (Z: 2)**:
   - Centered around Y: `650 - 850px`.
   - Asset types:
     - **3D Icons**: Fluent 3D icons (`assets/icons_3d/*.png`) with pop bounce spring physics.
     - **Code Editor Cards**: macOS IDE dark cards with traffic light buttons (`#FF5F56`, `#FFBD2E`, `#27C93F`), monospace font, line numbers, and glowing green/cyan syntax tokens.
     - **UI Mockups & Video Loops**: Framed modern SaaS cards with 16px corner radiuses and subtle drop shadows.
     - **Comparison Splits**: Old vs Modern split comparison layouts.
4. **Captions & Kinetic Typography (Z: 3)**:
   - Centered around Y: `1000 - 1200px`.
   - Primary Arabic Font: `IBMPlexSansArabic-Bold` or `Alexandria-Bold`.
   - Dual-tone active word highlighting: Active spoken word glows in high-contrast neon brand color (e.g., `#B7EC03`), while surrounding text stays clean `#FFFFFF`.
5. **Brand Anchors (Z: 4)**:
   - Brand logo / pill badge at top (`Y: 180 - 240px`).
   - Call to Action (CTA) or series badge at bottom (`Y: 1720 - 1800px`).

---

## 2. Pacing & Rhythm Presets

| Preset | Target Platform | Scene Duration | Caption Style | SFX Frequency | Best For |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`ultra_fast`** | TikTok, IG Gen-Z | 1.5s - 2.8s | 3-5 words per card, snappy scale punch | Every 1.0s - 1.5s (Hits, Glitches, Whooshes) | Teasers, shock facts, speed showdowns |
| **`fast_viral`** | Instagram Reels, Shorts | 3.0s - 4.5s | Full punchy sentences, word-by-word glow | Every scene transition + key emphasis | SaaS product reels, tips, case studies |
| **`cinematic_tech`** | YouTube, LinkedIn Tech | 5.0s - 8.0s | Smooth multi-line captions, continuous IDE typing | Subtle ambient pads, mechanical clicks | In-depth engineering breakdowns, architecture |

---

## 3. Motion Curves & Interpolation

- **Pop Bounce (Hero Assets)**:
  - Curve: Damped harmonic spring: $f(t) = 1 - e^{-\gamma t} \cdot \cos(\omega t)$.
  - Fast overshoot to `1.15x` scale in 120ms, settling to `1.0x` in 300ms.
- **Punch In (Hook / Climax)**:
  - Instant zoom scale jump `1.08x` on words like *"بص كده"*, *"تخيل"*, *"السر"*.
- **Camera Drift**:
  - Gentle linear or sinusoidal parallax drift restricted strictly to foreground elements. Background grid must remain fixed.

---

## 4. Sound Design & Audio Sync Contract

- **The 0.0s Hook Hit**: Always fire a high-impact cinematic sub-bass hit (`Hit.mp3`) at exact second 0.00.
- **Audio Hook Boost**: Boost the first 3.0 seconds of the voiceover track by `+4.0dB` to `+5.0dB` to cut through scrolling feeds.
- **Transition SFX**:
  - Scene cuts: `whoosh_fast.mp3` or `Air Whoosh 02.wav`.
  - Icon reveal / badge pop: `pop.mp3` or `ES_Camera Shutter Click`.
  - Bug / problem reveal: `mixkit-small-sci-fi-glitch-1030.wav` or `glitch-static`.
  - Cash / profit / speed: `cashier-quotka-chingquot` or `ES_Riser_Suction`.

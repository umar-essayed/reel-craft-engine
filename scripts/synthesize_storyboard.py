#!/usr/bin/env python3
"""
Reel Craft Engine - Project Synthesizer & Storyboard Generator
Takes a Whisper transcript JSON or raw text, selects appropriate pacing presets,
slices into scenes based on semantic pauses, assigns 3D icons, code cards, badge widgets,
and creates a ready-to-render project.json.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Builtin icon keyword mappings
ICON_KEYWORDS = {
    "speed": "zap.png",
    "سرعة": "zap.png",
    "سريع": "zap.png",
    "كيبورد": "keyboard.png",
    "لوحة": "keyboard.png",
    "شاشة": "monitor.png",
    "أجهزة": "cpu.png",
    "قديم": "hardware.png",
    "بطيء": "clock.png",
    "سحابة": "cloud.png",
    "كلاود": "cloud.png",
    "قفل": "lock.png",
    "أمان": "shield.png",
    "حماية": "shield.png",
    "كاشير": "cart.png",
    "فاتورة": "receipt.png",
    "مبيعات": "chart.png",
    "أرباح": "chart.png",
    "فكرة": "bulb.png",
    "كود": "code.png",
    "برمجة": "code.png",
    "نار": "fire.png",
    "صاروخ": "rocket.png",
    "ذكاء": "bulb.png",
    "إعدادات": "gear.png"
}

PACING_PRESETS = {
    "ultra_fast": {
        "description": "TikTok & Gen-Z ultra dynamic rhythm. Words flash in 0.18-0.3s bursts, snappy SFX on every punchline.",
        "max_words_per_scene": 10,
        "max_scene_duration": 3.0,
        "caption_animation": "scale_pop",
        "bg_drift_intensity": 1.2
    },
    "fast_viral": {
        "description": "Standard high-retention Instagram Reels / YouTube Shorts pace. 3-5s scenes, clear 3D widgets.",
        "max_words_per_scene": 16,
        "max_scene_duration": 4.5,
        "caption_animation": "spring_smooth",
        "bg_drift_intensity": 1.0
    },
    "cinematic_tech": {
        "description": "Polished Apple keynote style. Slower cuts, deep code card typing, smooth glow transitions.",
        "max_words_per_scene": 25,
        "max_scene_duration": 7.0,
        "caption_animation": "fade_slide",
        "bg_drift_intensity": 0.6
    }
}

def detect_icon_for_text(text: str) -> str:
    text_lower = text.lower()
    for kw, icon in ICON_KEYWORDS.items():
        if kw in text_lower:
            return icon
    return "bulb.png"

def synthesize_storyboard(transcript_data: dict, project_name: str, audio_path: str, pacing: str = "fast_viral", brand_info: dict = None) -> dict:
    preset = PACING_PRESETS.get(pacing, PACING_PRESETS["fast_viral"])
    words = transcript_data.get("words", [])
    
    if not words:
        raise ValueError("No word-level timings found in transcript!")

    total_duration = words[-1]["end"]
    
    # 1. Group words into scenes
    scenes = []
    current_scene_words = []
    scene_start = words[0]["start"]
    
    for i, w in enumerate(words):
        current_scene_words.append(w)
        
        # Check scene split conditions:
        is_last_word = (i == len(words) - 1)
        next_w = words[i + 1] if not is_last_word else None
        
        pause = (next_w["start"] - w["end"]) if next_w else 0.0
        duration_so_far = w["end"] - scene_start
        word_count = len(current_scene_words)
        
        # Split on significant pause (>0.45s) or exceeding scene limits
        should_split = (
            is_last_word or
            pause >= 0.45 or
            word_count >= preset["max_words_per_scene"] or
            duration_so_far >= preset["max_scene_duration"]
        )
        
        if should_split:
            scene_end = w["end"] + (0.15 if is_last_word else min(pause * 0.5, 0.2))
            scene_text = " ".join([cw["word"] for cw in current_scene_words])
            
            # Format word timing array for renderer
            w_sync = []
            for cw in current_scene_words:
                w_sync.append({
                    "word": cw["word"],
                    "start": round(cw["start"], 3),
                    "end": round(cw["end"], 3)
                })
                
            icon = detect_icon_for_text(scene_text)
            
            # Construct scene elements
            elements = [
                {
                    "type": "icon",
                    "source": f"assets/icons_3d/{icon}",
                    "size": 180,
                    "position": {"x": 540, "y": 700},
                    "animation": "pop_bounce",
                    "glow": True
                },
                {
                    "type": "text",
                    "text": scene_text,
                    "font_size": 52,
                    "color": "#FFFFFF",
                    "highlight_color": "#B7EC03",
                    "position": {"x": 540, "y": 1050},
                    "animation": preset["caption_animation"],
                    "word_sync": w_sync
                }
            ]
            
            scenes.append({
                "scene_id": f"scene_{len(scenes) + 1:02d}",
                "start_time": round(scene_start, 3),
                "end_time": round(scene_end, 3),
                "transition_in": "zoom_punch" if len(scenes) == 0 else "crossfade",
                "transition_out": "cut",
                "elements": elements
            })
            
            if next_w:
                scene_start = next_w["start"]
            current_scene_words = []

    # 2. Sound design track
    sfx_events = [
        {"file": "Hit.mp3", "time": 0.0, "volume": 1.0}
    ]
    for s in scenes[1:]:
        sfx_events.append({
            "file": "whoosh-blow-flutter-shortwav-14678.mp3",
            "time": round(s["start_time"], 2),
            "volume": 0.75
        })

    # Default brand styling
    brand = {
        "name": "BRAND",
        "tagline": "AI Motion Graphics Reel",
        "colors": {
            "primary": "#B7EC03",
            "secondary": "#00E5FF",
            "accent": "#B7EC03",
            "background": "#000000",
            "text_primary": "#FFFFFF",
            "highlight": "#B7EC03"
        }
    }
    if brand_info:
        brand.update(brand_info)

    project = {
        "project_name": project_name,
        "pacing_preset": pacing,
        "background_preset": "cyber_grid",
        "total_duration": round(total_duration + 0.5, 2),
        "settings": {
            "width": 1080,
            "height": 1920,
            "fps": 30,
            "total_duration": round(total_duration + 0.5, 2)
        },
        "brand": brand,
        "audio": {
            "voiceover": audio_path,
            "hook_boost_db": 4.0,
            "hook_duration": 3.0,
            "sfx": sfx_events
        },
        "scenes": scenes
    }
    return project

def main():
    parser = argparse.ArgumentParser(description="Generate Storyboard Project from Transcript")
    parser.add_argument("transcript_json", help="Path to transcript JSON file")
    parser.add_argument("--audio", "-a", required=True, help="Path to audio file (voiceover)")
    parser.add_argument("--output", "-o", default="project.json", help="Output project JSON path")
    parser.add_argument("--pacing", "-p", choices=list(PACING_PRESETS.keys()), default="fast_viral", help="Pacing preset")
    parser.add_argument("--name", "-n", default="Generated Reel", help="Project name")
    
    args = parser.parse_args()
    
    with open(args.transcript_json, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)
        
    project = synthesize_storyboard(
        transcript_data=transcript_data,
        project_name=args.name,
        audio_path=args.audio,
        pacing=args.pacing
    )
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)
        
    print(f"[+] Successfully generated project storyboard with {len(project['scenes'])} scenes.")
    print(f"[+] Pacing style: {args.pacing} ({PACING_PRESETS[args.pacing]['description']})")
    print(f"[+] Saved project file to: {args.output}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Reel Craft Engine - Unified Rendering CLI
Wraps export_project and audio mastering pipeline.
Accepts project.json and exports a high-bitrate 1080x1920 MP4 vertical reel with After Effects camera motions.
"""

import sys
import os
import argparse
from pathlib import Path

# Add skill root & engine to sys.path
SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))
sys.path.insert(0, str(SKILL_ROOT / "engine_core"))

try:
    from engine_core.config import load_project_config
    from engine_core.audio import build_master_audio
    from engine_core.exporter import export_project
    from engine_core.renderer import render_frame_by_config
except ImportError:
    from core.config import load_project_config
    from core.audio import build_master_audio
    from core.exporter import export_project
    from core.renderer import render_frame_by_config

def render_reel(project_path: str, output_path: str = None, preview_only: bool = False):
    project_file = os.path.abspath(project_path)
    config = load_project_config(project_file)
    
    if preview_only:
        print("[*] Generating preview stills...")
        for frame_idx in [0, 30, 90, 150]:
            img = render_frame_by_config(config, frame_idx)
            out_img = os.path.join(config.project_dir, f"preview_frame_{frame_idx}.png")
            img.save(out_img)
            print(f"[+] Saved preview: {out_img}")
        return
        
    audio_output = os.path.join(config.project_dir, "audio", "final_master_audio.wav")
    print(f"[*] Building master audio & SFX tracks: {audio_output}")
    build_master_audio(config, audio_output)
    
    print(f"[*] Exporting project to MP4 (1080x1920 @ {config.fps} FPS)...")
    final_video = export_project(
        config,
        output_mp4=output_path,
        master_audio_wav=audio_output
    )
    print(f"[+] Reel render complete: {final_video}")
    return final_video

def main():
    parser = argparse.ArgumentParser(description="Reel Craft Engine - Unified Reel Renderer")
    parser.add_argument("project", help="Path to project.json")
    parser.add_argument("--output", "-o", default=None, help="Output MP4 path")
    parser.add_argument("--preview", action="store_true", help="Generate preview still frames instead of full video")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.project):
        print(f"[!] Error: Project file '{args.project}' not found.", file=sys.stderr)
        sys.exit(1)
        
    render_reel(
        project_path=args.project,
        output_path=args.output,
        preview_only=args.preview
    )

if __name__ == "__main__":
    main()

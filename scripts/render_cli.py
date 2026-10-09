#!/usr/bin/env python3
"""
Reel Craft Engine - Unified Rendering CLI
Wraps reel_engine renderer and audio mastering pipeline.
Accepts project.json and exports a high-bitrate 1080x1920 MP4 vertical reel.
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
    from engine_core.renderer import ReelRenderer
    from engine_core.audio import AudioMaster
except ImportError:
    # Fallback to local workspace if running from repo
    from core.renderer import ReelRenderer
    from core.audio import AudioMaster

def render_reel(project_path: str, output_path: str = None, threads: int = 8, preview_only: bool = False):
    project_file = os.path.abspath(project_path)
    project_dir = os.path.dirname(project_file)
    
    if not output_path:
        base_name = Path(project_file).stem
        output_dir = os.path.join(project_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{base_name}_reel.mp4")
    else:
        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
    print(f"[*] Initializing ReelRenderer for: {project_file}")
    renderer = ReelRenderer(project_file)
    
    if preview_only:
        print("[*] Generating preview stills...")
        renderer.render_preview(frame_indices=[0, 30, 90, 150])
        print("[+] Previews generated.")
        return output_path
        
    print(f"[*] Starting full rendering to: {output_path}")
    print(f"[*] Thread count: {threads}")
    
    # Render video track
    temp_video = renderer.render(output_path=output_path, num_workers=threads)
    
    print(f"[+] Reel render complete: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Reel Craft Engine - Unified Reel Renderer")
    parser.add_argument("project", help="Path to project.json")
    parser.add_argument("--output", "-o", default=None, help="Output MP4 path")
    parser.add_argument("--threads", "-t", type=int, default=8, help="Number of render worker threads")
    parser.add_argument("--preview", action="store_true", help="Generate preview still frames instead of full video")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.project):
        print(f"[!] Error: Project file '{args.project}' not found.", file=sys.stderr)
        sys.exit(1)
        
    render_reel(
        project_path=args.project,
        output_path=args.output,
        threads=args.threads,
        preview_only=args.preview
    )

if __name__ == "__main__":
    main()

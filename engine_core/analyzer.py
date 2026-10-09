import os
import subprocess
import numpy as np
from typing import Dict, Any, List, Optional
from PIL import Image

def analyze_audio_local(audio_path: str) -> Dict[str, Any]:
    """
    Analyzes audio locally using FFmpeg/NumPy (Zero Token Cost).
    Extracts duration, peak amplitude, silence pauses, and recommends scene cut points.
    """
    if not audio_path or not os.path.exists(audio_path):
        return {"error": "Audio file not found"}

    # 1. Probe duration
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        duration = float(res.stdout.strip())
    except Exception:
        duration = 14.0

    # 2. Extract waveform energy to find speech silence / pause points
    pcm_cmd = [
        "ffmpeg", "-y", "-i", audio_path,
        "-f", "s16le", "-ac", "1", "-ar", "8000", "pipe:1"
    ]
    pcm_res = subprocess.run(pcm_cmd, capture_output=True)
    energy_points = []
    recommended_cuts = [0.0]

    if pcm_res.returncode == 0 and len(pcm_res.stdout) > 0:
        samples = np.frombuffer(pcm_res.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        # Window of 200ms = 1600 samples
        win_size = 1600
        num_windows = len(samples) // win_size
        energies = []
        for w_idx in range(num_windows):
            chunk = samples[w_idx * win_size : (w_idx + 1) * win_size]
            rms = float(np.sqrt(np.mean(chunk**2)))
            energies.append(rms)

        # Detect pauses (low energy valley between speech chunks)
        threshold = max(0.015, np.mean(energies) * 0.4)
        last_cut = 0.0
        for i in range(1, len(energies) - 1):
            t_sec = round((i * win_size) / 8000.0, 2)
            if energies[i] < threshold and (t_sec - last_cut) >= 2.4:
                recommended_cuts.append(t_sec)
                last_cut = t_sec

    if duration > (recommended_cuts[-1] + 1.5):
        recommended_cuts.append(round(duration, 2))

    # Auto-generate scene segments
    scenes_proposal = []
    for idx in range(len(recommended_cuts) - 1):
        s_start = recommended_cuts[idx]
        s_end = recommended_cuts[idx + 1]
        scenes_proposal.append({
            "scene_num": idx + 1,
            "start": s_start,
            "end": s_end,
            "duration": round(s_end - s_start, 2),
            "suggested_type": "cta" if (idx == len(recommended_cuts) - 2) else "standard"
        })

    return {
        "audio_file": os.path.basename(audio_path),
        "duration": round(duration, 2),
        "speech_cut_points": recommended_cuts,
        "recommended_scenes": scenes_proposal,
        "hook_duration": min(3.0, duration)
    }

def analyze_image_local(image_path: str) -> Dict[str, Any]:
    """
    Inspects an image locally: dimensions, aspect ratio, and extracts dominant vibrant brand colors.
    Uses saturation and edge/corner background rejection to ensure real brand colors are chosen,
    never dull background greys or anti-aliased edge artifacts.
    """
    if not image_path or not os.path.exists(image_path):
        return {"error": "Image file not found"}

    try:
        img = Image.open(image_path).convert("RGBA")
        w, h = img.size
        aspect_ratio = round(w / h, 2)

        # 1. Resize for fast color analysis
        small = img.resize((64, 64), Image.Resampling.BOX)
        pixels = list(small.getdata())

        # 2. Sample corner pixels to detect solid background color
        corners = [
            pixels[0], pixels[63], pixels[64 * 63], pixels[64 * 64 - 1],
            pixels[1], pixels[62], pixels[64 * 63 + 1], pixels[64 * 64 - 2]
        ]
        # Find corner majority color if opaque
        corner_colors = [(r, g, b) for r, g, b, a in corners if a > 200]
        bg_color = None
        if corner_colors:
            from collections import Counter
            c_counts = Counter(corner_colors)
            most_c, c_freq = c_counts.most_common(1)[0]
            if c_freq >= 3:
                bg_color = most_c

        # 3. Analyze pixels and score by saturation
        bins = {} # (r_bin, g_bin, b_bin) -> score
        bin_representatives = {}

        for r, g, b, a in pixels:
            # Skip transparent pixels
            if a < 120:
                continue

            # Skip background color if detected
            if bg_color:
                dist = abs(r - bg_color[0]) + abs(g - bg_color[1]) + abs(b - bg_color[2])
                if dist < 45:
                    continue

            max_c = max(r, g, b)
            min_c = min(r, g, b)
            delta = max_c - min_c
            luminance = 0.299 * r + 0.587 * g + 0.114 * b

            # Skip extreme near-black or extreme near-white
            if luminance < 12 or luminance > 248:
                continue

            # Calculate Saturation (0.0 to 1.0)
            sat = delta / (max_c + 1e-4)

            # Skip dull grey/muddy pixels if they have almost no color saturation
            if sat < 0.15 and not (30 < luminance < 220 and delta > 15):
                continue

            # Quantize to bins of 20
            r_bin = (r // 20) * 20 + 10
            g_bin = (g // 20) * 20 + 10
            b_bin = (b // 20) * 20 + 10
            bin_key = (r_bin, g_bin, b_bin)

            # Score: frequency weighted heavily by saturation
            score = 1.0 + (sat * 4.0) + (1.0 if (40 < luminance < 210) else 0.2)
            bins[bin_key] = bins.get(bin_key, 0.0) + score
            if bin_key not in bin_representatives:
                bin_representatives[bin_key] = (r, g, b)

        sorted_bins = sorted(bins.items(), key=lambda x: x[1], reverse=True)
        dominant_hex = []

        for (b_key, b_score) in sorted_bins:
            r, g, b = bin_representatives[b_key]
            hex_c = f"#{r:02x}{g:02x}{b:02x}".upper()
            # Ensure color distance from already chosen colors
            is_distinct = True
            for existing in dominant_hex:
                er = int(existing[1:3], 16)
                eg = int(existing[3:5], 16)
                eb = int(existing[5:7], 16)
                c_dist = abs(r - er) + abs(g - eg) + abs(b - eb)
                if c_dist < 60:
                    is_distinct = False
                    break
            if is_distinct:
                dominant_hex.append(hex_c)
            if len(dominant_hex) >= 3:
                break

        # Fallback to stylish defaults if logo is pure monochrome or no color found
        if not dominant_hex:
            dominant_hex = ["#FF8A00", "#0143A3", "#00D2FF"]
        elif len(dominant_hex) == 1:
            dominant_hex.append("#0143A3")
            dominant_hex.append("#00D2FF")
        elif len(dominant_hex) == 2:
            dominant_hex.append("#00D2FF")

        return {
            "file_name": os.path.basename(image_path),
            "width": w,
            "height": h,
            "aspect_ratio": aspect_ratio,
            "recommended_type": "mockup_phone" if aspect_ratio < 0.8 else ("mockup_desktop" if aspect_ratio > 1.3 else "banner"),
            "extracted_brand_palette": {
                "primary": dominant_hex[0],
                "secondary": dominant_hex[1],
                "accent": dominant_hex[2]
            }
        }
    except Exception as e:
        return {"error": str(e)}

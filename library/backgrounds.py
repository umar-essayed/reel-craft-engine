import os
import math
import numpy as np
from PIL import Image, ImageDraw

def render_background_preset(preset_name: str, width: int = 1080, height: int = 1920,
                             primary_color=(73, 32, 240), secondary_color=(183, 236, 3),
                             bg_color=(3, 4, 7), t: float = 0.0) -> Image.Image:
    """
    Renders dynamic high-end procedural backgrounds without needing external video files.
    """
    canvas = Image.new("RGBA", (width, height), bg_color + (255,))
    draw = ImageDraw.Draw(canvas)

    # 1. Cyber Tech Grid + Glowing Floating Tech Particles (Rock-Solid Static Grid + Glowing Floating Embers)
    if preset_name in ("cyber_grid", "default", "cyber_particles", "particles_glow"):
        # Elegant square size
        grid_size = 120
        # Ultra-subtle, clean, stable white hairline grid (opacity 18/255, 100% static)
        grid_col = (255, 255, 255, 18)

        # Vertical grid lines (hairline 1px, 100% static)
        for x in range(0, width, grid_size):
            draw.line((x, 0, x, height), fill=grid_col, width=1)

        # Horizontal grid lines (hairline 1px, 100% static)
        for y in range(0, height, grid_size):
            draw.line((0, y, width, y), fill=grid_col, width=1)

        # Glowing floating tech particles (Smooth pulsing glow)
        num_particles = 32
        for i in range(num_particles):
            seed_x = ((i * 137) % width)
            seed_y = ((i * 241) % height)
            speed = 22.0 + (i % 5) * 10.0
            p_size = 2 + (i % 3)

            cur_y = int((seed_y - t * speed) % height)
            cur_x = int(seed_x + math.sin(t * 1.5 + i) * 16.0) % width

            # Smooth glowing pulse
            pulse = 0.5 + 0.5 * math.sin(t * 2.2 + i * 0.9)
            p_alpha = int((0.35 + 0.65 * pulse) * 180)

            col = (secondary_color if (i % 2 == 0) else primary_color)
            # Soft glowing halo
            draw.ellipse((cur_x - p_size * 2, cur_y - p_size * 2, cur_x + p_size * 2, cur_y + p_size * 2), fill=col + (int(p_alpha * 0.25),))
            # Core
            draw.ellipse((cur_x - p_size, cur_y - p_size, cur_x + p_size, cur_y + p_size), fill=col + (p_alpha,))

    # 2. Studio Radial Spotlight (Cinematic Vignette)
    elif preset_name in ("studio_minimal", "spotlight"):
        cx, cy = width // 2, height // 2
        max_r = int(math.hypot(cx, cy))
        for r in range(max_r, 0, -35):
            alpha = int((1.0 - (r / max_r)) * 40)
            spot_color = primary_color + (alpha,)
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=spot_color)

    # 3. Code Stream (Subtle matrix-like dark cyber stream)
    elif preset_name == "code_stream":
        # Draw dark grid first
        for x in range(0, width, 140):
            draw.line((x, 0, x, height), fill=(255, 255, 255, 12), width=1)
        for col_idx in range(12):
            col_x = 90 + col_idx * 75
            col_speed = 60.0 + (col_idx % 4) * 25.0
            head_y = int((t * col_speed + col_idx * 160) % (height + 300)) - 100
            for trail_i in range(8):
                ty = head_y - trail_i * 22
                if 0 <= ty < height:
                    t_alpha = int((1.0 - trail_i / 8.0) * 120)
                    draw.rectangle((col_x, ty, col_x + 8, ty + 14), fill=secondary_color + (t_alpha,))

    # 4. Aurora Glow (Modern Tech Organic Waves)
    elif preset_name == "aurora_glow":
        for y in range(0, height, 120):
            shift = math.sin((y / 200.0) + (t * 1.5)) * 40
            draw.arc((int(shift) - 200, y - 100, width + int(shift) + 200, y + 100),
                     start=0, end=180, fill=(16, 185, 129, 22), width=8)
            draw.arc((int(-shift) - 150, y - 80, width + int(-shift) + 150, y + 80),
                     start=180, end=360, fill=(6, 182, 212, 18), width=6)

    # 5. Sunset Neon (Royal Violet to Warm Amber)
    elif preset_name == "sunset_neon":
        grad = Image.new("RGBA", (width, height), (15, 10, 30, 255))
        g_draw = ImageDraw.Draw(grad)
        for y in range(height):
            ratio = y / height
            r = int(25 + ratio * 40)
            g = int(10 + ratio * 15)
            b = int(45 - ratio * 20)
            g_draw.line((0, y, width, y), fill=(r, g, b, 255))
        canvas = grad

    # 6. Brand Custom Radial
    elif preset_name == "brand_custom":
        cx, cy = width // 2, int(height * 0.45)
        for r in range(900, 0, -30):
            ratio = 1.0 - (r / 900.0)
            alpha = int(ratio * 38)
            glow_c = primary_color + (alpha,)
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=glow_c)

    return canvas

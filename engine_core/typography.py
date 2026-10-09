import os
import math
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920

SAFE_MARGIN_X = 90
SAFE_MAX_WIDTH = CANVAS_WIDTH - (SAFE_MARGIN_X * 2) # 900px safe width
SAFE_MARGIN_TOP = 180
SAFE_MARGIN_BOTTOM = 1720

def get_text_size(text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    if not text:
        return (0, 0)
    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font, direction="rtl")
    if bbox:
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])
    return (len(text) * 20, 40)

def wrap_arabic_text(text: str, font: ImageFont.ImageFont, max_width: int = SAFE_MAX_WIDTH) -> List[str]:
    """
    Intelligently wraps Arabic text into clean, balanced lines without breaking words.
    Respects RTL sentence structure.
    """
    words = text.strip().split()
    if not words:
        return []

    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        w, _ = get_text_size(test_line, font)
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                # Single word exceeds max_width
                lines.append(word)
                current_line = []

    if current_line:
        lines.append(" ".join(current_line))

    return lines

def auto_fit_text(text: str, get_font_fn, initial_size: int = 72,
                  max_width: int = SAFE_MAX_WIDTH, max_lines: int = 3,
                  min_size: int = 34) -> Tuple[ImageFont.ImageFont, List[str]]:
    """
    Automatically scales font size down until text fits within max_width and max_lines.
    Guarantees no text ever overflows the screen margins.
    """
    size = initial_size
    while size >= min_size:
        font = get_font_fn(size)
        lines = wrap_arabic_text(text, font, max_width=max_width)
        if len(lines) <= max_lines:
            return font, lines
        size -= 4

    font = get_font_fn(min_size)
    lines = wrap_arabic_text(text, font, max_width=max_width)
    return font, lines

def draw_animated_text(canvas: Image.Image,
                       text: str,
                       pos: Tuple[int, int],
                       font_fn,
                       size: int = 70,
                       color: Tuple[int, int, int] = (255, 255, 255),
                       highlight_color: Tuple[int, int, int] = (255, 189, 46),
                       animation: str = "typewriter",
                       progress: float = 1.0,
                       max_width: int = SAFE_MAX_WIDTH,
                       line_spacing: int = 24) -> Image.Image:
    """
    Renders text with strict safe margins, auto-wrapping, and motion animation styles:
    - typewriter: Characters type out with realistic pacing.
    - elastic_bounce: Elastic scale-in with overshoot bounce.
    - karaoke: Highlight words sequentially in sync with speech progress.
    - fade_up: Smooth upward float with alpha transition.
    - static: Direct clean rendering.
    """
    if progress <= 0.001 or not text:
        return canvas

    font, lines = auto_fit_text(text, font_fn, initial_size=size, max_width=max_width)
    cx, base_cy = pos

    # Calculate total block height
    dummy_font = font
    _, line_h = get_text_size("تجربة", dummy_font)
    line_step = line_h + line_spacing
    total_block_h = len(lines) * line_step
    start_y = base_cy - (total_block_h // 2)

    # 1. Typewriter Animation
    if animation == "typewriter":
        total_chars = sum(len(l) for l in lines)
        visible_chars = max(1, int(total_chars * min(1.0, progress)))
        
        draw = ImageDraw.Draw(canvas)
        chars_drawn = 0
        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step)
            if chars_drawn >= visible_chars:
                break
            remain = visible_chars - chars_drawn
            display_line = line[:remain]
            chars_drawn += len(line)
            draw.text((cx, line_y), display_line, fill=color + (255,), font=font, direction="rtl", anchor="mm")

    # 2. Elastic Bounce (Physical scale overshoot)
    elif animation in ("elastic_bounce", "pop_in"):
        p = min(1.0, progress * 1.5)
        # Elastic curve: overshoot from 0.7 to 1.1 then settle to 1.0
        scale = 1.0 + 0.35 * math.exp(-6.0 * p) * math.cos(12.0 * p) if p < 1.0 else 1.0
        alpha = int(min(255, max(0, progress * 4.0 * 255)))

        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step)
            draw.text((cx, line_y), line, fill=color + (alpha,), font=font, direction="rtl", anchor="mm")

        if abs(scale - 1.0) > 0.01:
            w, h = canvas.size
            scaled_w = int(w * scale)
            scaled_h = int(h * scale)
            res = layer.resize((scaled_w, scaled_h), Image.Resampling.BILINEAR)
            # Paste centered
            ox = (w - scaled_w) // 2
            oy = (h - scaled_h) // 2
            return Image.alpha_composite(canvas, res.crop((-ox, -oy, w - ox, h - oy)))
        return Image.alpha_composite(canvas, layer)

    # 3. Karaoke / Word-by-Word Highlight (Viral Subtitle with glowing active word)
    elif animation in ("karaoke", "word_highlight", "word_pop", "hormozi_pop"):
        draw = ImageDraw.Draw(canvas)
        all_words = []
        for l_idx, l in enumerate(lines):
            for w in l.split():
                all_words.append((w, l_idx))

        total_words = max(1, len(all_words))
        # Ensure active word sweeps cleanly across all words during scene speech
        active_idx = min(total_words - 1, max(0, int(progress * total_words)))

        current_w_idx = 0
        for l_idx, line in enumerate(lines):
            line_words = line.split()
            line_y = start_y + (l_idx * line_step)

            # Measure full line accurately for perfect horizontal center
            full_w, line_h = get_text_size(" ".join(line_words), font)
            cursor_x = cx + (full_w // 2)

            for w in line_words:
                w_w, w_h = get_text_size(w, font)
                space_w, _ = get_text_size(" ", font)
                is_active = (current_w_idx == active_idx)
                is_past = (current_w_idx < active_idx)

                # Word right edge is cursor_x, left edge is cursor_x - w_w
                w_left = cursor_x - w_w
                w_right = cursor_x
                w_mid_x = (w_left + w_right) // 2

                if is_active:
                    # Active spoken word: Vibrant fluorescent lime with glowing aura + drop shadow
                    # 1. Deep black shadow
                    draw.text((cursor_x + 4, line_y + 4), w, fill=(0, 0, 0, 255), font=font, direction="rtl", anchor="rm")
                    # 2. Soft fluorescent lime neon glow passes
                    for ox, oy in ((-3,0), (3,0), (0,-3), (0,3), (-2,-2), (2,2), (-2,2), (2,-2)):
                        draw.text((cursor_x + ox, line_y + oy), w, fill=(183, 236, 3, 120), font=font, direction="rtl", anchor="rm")
                    # 3. Crisp vibrant lime active word on top
                    draw.text((cursor_x, line_y), w, fill=highlight_color + (255,), font=font, direction="rtl", anchor="rm")
                elif is_past:
                    # Spoken past words: Crisp bright white with deep ambient shadow
                    draw.text((cursor_x + 3, line_y + 4), w, fill=(0, 0, 0, 240), font=font, direction="rtl", anchor="rm")
                    draw.text((cursor_x, line_y), w, fill=(255, 255, 255, 255), font=font, direction="rtl", anchor="rm")
                else:
                    # Upcoming words: Muted clean off-white / silver
                    draw.text((cursor_x + 2, line_y + 3), w, fill=(0, 0, 0, 180), font=font, direction="rtl", anchor="rm")
                    draw.text((cursor_x, line_y), w, fill=(180, 195, 210, 200), font=font, direction="rtl", anchor="rm")

                cursor_x -= (w_w + space_w)
                current_w_idx += 1
        return canvas

    # 4. Fade Up Float
    elif animation == "fade_up":
        p = min(1.0, progress * 1.4)
        offset_y = int((1.0 - p) * 45) # float up 45px
        alpha = int(min(255, max(0, p * 255)))
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step) - offset_y
            draw.text((cx + 3, line_y + 3), line, fill=(0, 0, 0, int(alpha * 0.8)), font=font, direction="rtl", anchor="mm")
            draw.text((cx, line_y), line, fill=color + (alpha,), font=font, direction="rtl", anchor="mm")
        return Image.alpha_composite(canvas, layer)

    # 5. Zoom Slam / Impact (Dramatic rapid scale down onto screen)
    elif animation in ("zoom_slam", "impact_slam", "slam"):
        p = min(1.0, progress * 2.2)
        if p < 0.6:
            scale = 2.2 - (1.2 * (p / 0.6))
        else:
            scale = 1.0 + 0.08 * math.sin((p - 0.6) * 15.0) * math.exp(-(p - 0.6) * 6.0)
        alpha = int(min(255, max(0, p * 2.5 * 255)))

        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step)
            draw.text((cx + 4, line_y + 4), line, fill=(0, 0, 0, int(alpha * 0.85)), font=font, direction="rtl", anchor="mm")
            draw.text((cx, line_y), line, fill=color + (alpha,), font=font, direction="rtl", anchor="mm")

        if abs(scale - 1.0) > 0.01:
            w, h = canvas.size
            scaled_w = max(10, int(w * scale))
            scaled_h = max(10, int(h * scale))
            res = layer.resize((scaled_w, scaled_h), Image.Resampling.BILINEAR)
            ox = (w - scaled_w) // 2
            oy = (h - scaled_h) // 2
            return Image.alpha_composite(canvas, res.crop((-ox, -oy, w - ox, h - oy)))
        return Image.alpha_composite(canvas, layer)

    # 6. Glow Pulse (Neon glowing aura around text with soft breathing)
    elif animation in ("glow_pulse", "neon_glow", "pulse"):
        p = min(1.0, progress * 2.0)
        pulse = 0.5 + 0.5 * math.sin(progress * 7.0)
        glow_alpha = int(80 + 100 * pulse)
        
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        
        # Soft outer glow passes
        glow_col = highlight_color + (glow_alpha // 3,)
        for r in (8, 5, 3):
            for dx, dy in ((-r,0),(r,0),(0,-r),(0,r),(-r,-r),(r,r)):
                for idx, line in enumerate(lines):
                    line_y = start_y + (idx * line_step)
                    draw.text((cx + dx, line_y + dy), line, fill=glow_col, font=font, direction="rtl", anchor="mm")
        
        # Main text on top
        main_alpha = int(min(255, max(0, p * 255)))
        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step)
            draw.text((cx + 3, line_y + 3), line, fill=(0, 0, 0, int(main_alpha * 0.85)), font=font, direction="rtl", anchor="mm")
            draw.text((cx, line_y), line, fill=color + (main_alpha,), font=font, direction="rtl", anchor="mm")
        return Image.alpha_composite(canvas, layer)

    # 7. Slide In Lateral (High-energy horizontal swipe)
    elif animation in ("slide_left", "slide_in", "swipe"):
        p = min(1.0, progress * 1.6)
        ease_p = 1.0 - math.pow(1.0 - p, 3) # Cubic ease out
        offset_x = int((1.0 - ease_p) * 260) # swipe from right to left
        alpha = int(min(255, max(0, p * 255)))
        
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step)
            draw.text((cx - offset_x + 3, line_y + 3), line, fill=(0, 0, 0, int(alpha * 0.85)), font=font, direction="rtl", anchor="mm")
            draw.text((cx - offset_x, line_y), line, fill=color + (alpha,), font=font, direction="rtl", anchor="mm")
        return Image.alpha_composite(canvas, layer)

    # 8. Box Highlight (Dynamic viral colored background card behind each line)
    elif animation in ("box_highlight", "card_pop", "highlight_box"):
        p = min(1.0, progress * 1.8)
        alpha = int(min(255, max(0, p * 255)))
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step)
            lw, lh = get_text_size(line, font)
            pad_x, pad_y = 32, 16
            bx1, by1 = cx - (lw // 2) - pad_x, line_y - (lh // 2) - pad_y
            bx2, by2 = cx + (lw // 2) + pad_x, line_y + (lh // 2) + pad_y
            
            # Animate box expanding width
            cur_w = (bx2 - bx1) * p
            cur_bx1 = cx - (cur_w // 2)
            cur_bx2 = cx + (cur_w // 2)
            
            draw.rounded_rectangle((cur_bx1, by1, cur_bx2, by2), radius=16, fill=(10, 15, 28, int(alpha * 0.95)), outline=highlight_color + (alpha,), width=2)
            if p > 0.3:
                txt_alpha = int(min(255, (p - 0.3) / 0.7 * 255))
                draw.text((cx + 3, line_y + 3), line, fill=(0, 0, 0, int(txt_alpha * 0.8)), font=font, direction="rtl", anchor="mm")
                draw.text((cx, line_y), line, fill=color + (txt_alpha,), font=font, direction="rtl", anchor="mm")
        return Image.alpha_composite(canvas, layer)

    # 9. Glitch / Cyber Twitch
    elif animation in ("glitch", "cyber_glitch"):
        p = min(1.0, progress * 2.0)
        alpha = int(min(255, max(0, p * 255)))
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        
        twitch_x = int(math.sin(progress * 40.0) * 12) if progress < 0.35 else 0
        if twitch_x != 0:
            for idx, line in enumerate(lines):
                line_y = start_y + (idx * line_step)
                draw.text((cx + twitch_x, line_y), line, fill=(183, 236, 3, alpha // 2), font=font, direction="rtl", anchor="mm")
                draw.text((cx - twitch_x, line_y), line, fill=(255, 255, 255, alpha // 2), font=font, direction="rtl", anchor="mm")
        
        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step)
            draw.text((cx + 3, line_y + 3), line, fill=(0, 0, 0, int(alpha * 0.85)), font=font, direction="rtl", anchor="mm")
            draw.text((cx, line_y), line, fill=color + (alpha,), font=font, direction="rtl", anchor="mm")
        return Image.alpha_composite(canvas, layer)

    # 10. Word Pop (Viral Subtitle: spoken word glows in fluorescent lime #B7EC03)
    elif animation in ("word_pop", "hormozi_pop"):
        draw = ImageDraw.Draw(canvas)
        all_words = []
        for l_idx, l in enumerate(lines):
            for w in l.split():
                all_words.append((w, l_idx))
        total_w = max(1, len(all_words))
        active_w_idx = min(total_w - 1, int(progress * total_w * 1.15))

        cur_idx = 0
        for l_idx, line in enumerate(lines):
            line_words = line.split()
            line_y = start_y + (l_idx * line_step)
            full_w, _ = get_text_size(" ".join(line_words), font)
            cursor_x = cx + (full_w // 2)

            for w in line_words:
                w_width, w_h = get_text_size(w + " ", font)
                if cur_idx <= active_w_idx:
                    is_active = (cur_idx == active_w_idx)
                    if is_active:
                        # Spoken active word is highlighted in fluorescent lime with glow
                        draw.text((cursor_x + 3, line_y + 3), w, fill=(0, 0, 0, 240), font=font, direction="rtl", anchor="rm")
                        draw.text((cursor_x, line_y), w, fill=highlight_color + (255,), font=font, direction="rtl", anchor="rm")
                    else:
                        # Spoken past words are clean white with drop shadow
                        draw.text((cursor_x + 3, line_y + 3), w, fill=(0, 0, 0, 200), font=font, direction="rtl", anchor="rm")
                        draw.text((cursor_x, line_y), w, fill=color + (255,), font=font, direction="rtl", anchor="rm")
                else:
                    # Upcoming words in clean muted light gray
                    draw.text((cursor_x, line_y), w, fill=(120, 130, 145, 180), font=font, direction="rtl", anchor="rm")
                cursor_x -= w_width
                cur_idx += 1
        return canvas

    # 11. Shake Intense (High-energy camera/text shock for hooks)
    elif animation in ("shake_intense", "camera_shake", "shock"):
        p = min(1.0, progress * 2.5)
        alpha = int(min(255, max(0, p * 255)))
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        shake_mag = int(max(0, (1.0 - progress * 2.0)) * 24)
        ox = int(math.sin(progress * 55.0) * shake_mag)
        oy = int(math.cos(progress * 48.0) * (shake_mag // 2))

        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step)
            draw.text((cx + ox, line_y + oy), line, fill=color + (alpha,), font=font, direction="rtl", anchor="mm")
        return Image.alpha_composite(canvas, layer)

    # 12. Neon Flicker (Fluorescent tube ignition flickering)
    elif animation in ("neon_flicker", "flicker"):
        # Realistic tube flicker sequence at startup
        flicker_on = True
        if progress < 0.35:
            cycle = int(progress * 28.0)
            flicker_on = (cycle % 2 == 0) or (cycle % 5 == 0)

        alpha = 255 if flicker_on else 35
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        glow_c = highlight_color + (int(alpha * 0.45),)

        if flicker_on:
            for r in (6, 3):
                for dx, dy in ((-r,0),(r,0),(0,-r),(0,r)):
                    for idx, line in enumerate(lines):
                        line_y = start_y + (idx * line_step)
                        draw.text((cx + dx, line_y + dy), line, fill=glow_c, font=font, direction="rtl", anchor="mm")

        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step)
            draw.text((cx, line_y), line, fill=color + (alpha,), font=font, direction="rtl", anchor="mm")
        return Image.alpha_composite(canvas, layer)

    # 13. Slide Up Reveal (Theatrical curtain pop)
    elif animation in ("slide_up_reveal", "slide_up"):
        p = min(1.0, progress * 1.8)
        ease = 1.0 - math.pow(1.0 - p, 4)
        offset_y = int((1.0 - ease) * 80)
        alpha = int(min(255, max(0, p * 255)))

        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step) + offset_y
            draw.text((cx, line_y), line, fill=color + (alpha,), font=font, direction="rtl", anchor="mm")
        return Image.alpha_composite(canvas, layer)

    # 14. Color Cycle / Shimmer (Dynamic multi-color gradient shimmer)
    elif animation in ("color_cycle", "shimmer"):
        p = min(1.0, progress * 2.0)
        alpha = int(min(255, max(0, p * 255)))
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)

        cycle_phase = (math.sin(progress * 6.0) + 1.0) / 2.0 # 0 to 1
        # Blend color and highlight_color
        r_bl = int(color[0] * (1 - cycle_phase) + highlight_color[0] * cycle_phase)
        g_bl = int(color[1] * (1 - cycle_phase) + highlight_color[1] * cycle_phase)
        b_bl = int(color[2] * (1 - cycle_phase) + highlight_color[2] * cycle_phase)
        bl_col = (r_bl, g_bl, b_bl, alpha)

        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step)
            draw.text((cx, line_y), line, fill=bl_col, font=font, direction="rtl", anchor="mm")
        return Image.alpha_composite(canvas, layer)

    # 15. Static / Clean
    else:
        draw = ImageDraw.Draw(canvas)
        for idx, line in enumerate(lines):
            line_y = start_y + (idx * line_step)
            draw.text((cx, line_y), line, fill=color + (255,), font=font, direction="rtl", anchor="mm")

    return canvas

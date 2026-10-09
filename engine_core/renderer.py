import os
import math
import numpy as np
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .config import (
    ProjectConfig, TextElement, PillElement, MockupElement, SceneConfig, hex_to_rgb,
    IconElement, CodeCardElement, ComparisonElement, BadgeWidgetElement
)
from .c_accelerator import generate_procedural_background, fast_blend_rgba

_FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}
_IMAGE_CACHE: Dict[str, Image.Image] = {}
_BG_CACHE: Dict[str, Image.Image] = {}

def get_font(font_size: int, project_dir: Optional[str] = None) -> ImageFont.ImageFont:
    """Finds and caches the best Arabic-supporting font available."""
    cache_key = (str(project_dir), font_size)
    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]

    search_dirs = []
    if project_dir:
        search_dirs.append(os.path.join(project_dir, "assets", "fonts"))
        search_dirs.append(os.path.join(project_dir, "fonts"))
    # Global search paths
    search_dirs.extend([
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")),
        "/usr/share/fonts/truetype/noto",
        "/usr/share/fonts/opentype/noto",
        "/usr/share/fonts/truetype/dejavu"
    ])

    preferred_fonts = [
        "Tajawal-Black.ttf",
        "Tajawal-Bold.ttf",
        "NotoSansArabic-Bold.ttf",
        "NotoKufiArabic-Bold.ttf",
        "DejaVuSans-Bold.ttf"
    ]

    for d in search_dirs:
        if os.path.exists(d):
            for pf in preferred_fonts:
                p = os.path.join(d, pf)
                if os.path.exists(p):
                    try:
                        font = ImageFont.truetype(p, font_size)
                        _FONT_CACHE[cache_key] = font
                        return font
                    except Exception:
                        pass

    font = ImageFont.load_default()
    _FONT_CACHE[cache_key] = font
    return font

def clear_caches():
    """Clears in-memory image and font caches when projects or assets are updated."""
    _IMAGE_CACHE.clear()
    _FONT_CACHE.clear()

def load_cached_image(file_path: str) -> Optional[Image.Image]:
    if not file_path or not os.path.exists(file_path):
        return None
    if file_path in _IMAGE_CACHE:
        return _IMAGE_CACHE[file_path].copy()
    try:
        img = Image.open(file_path).convert("RGBA")
        _IMAGE_CACHE[file_path] = img
        return img.copy()
    except Exception:
        return None

def get_base_background(config: ProjectConfig, t: float = 0.0, preset_override: Optional[str] = None) -> Image.Image:
    w, h = config.width, config.height
    cache_key = f"{config.project_dir}_{w}_{h}"
    
    if config.background_image and os.path.exists(config.background_image):
        if cache_key in _BG_CACHE:
            return _BG_CACHE[cache_key].copy()
        bg = Image.open(config.background_image).convert("RGBA")
        bg = bg.resize((w, h), Image.Resampling.LANCZOS)
        
        # Soft dark overlay from brand background color (85% opacity)
        bg_rgb = config.brand.colors.background
        overlay = Image.new("RGBA", (w, h), bg_rgb + (215,))
        base = Image.alpha_composite(bg, overlay)
        
        # Draw tech grid lines
        draw = ImageDraw.Draw(base)
        grid_size = 80
        grid_color = config.brand.colors.secondary + (25,)
        for x in range(0, w, grid_size):
            draw.line((x, 0, x, h), fill=grid_color)
        for y in range(0, h, grid_size):
            draw.line((0, y, w, y), fill=grid_color)
            
        _BG_CACHE[cache_key] = base
        return _BG_CACHE[cache_key].copy()

    # Procedural background shader or preset
    try:
        from ..library.backgrounds import render_background_preset
    except (ImportError, ValueError):
        try:
            from library.backgrounds import render_background_preset
        except (ImportError, ValueError):
            from reel_engine.library.backgrounds import render_background_preset
    preset_name = preset_override or getattr(config, "background_preset", "cyber_grid") or "cyber_grid"
    
    # Cache static background only if not animated preset
    if preset_name in ("cyber_grid", "default") and t == 0.0:
        preset_cache_key = f"preset_{preset_name}_{w}_{h}_{config.brand.colors.background}"
        if preset_cache_key in _BG_CACHE:
            return _BG_CACHE[preset_cache_key].copy()
        bg = render_background_preset(
            preset_name=preset_name,
            width=w,
            height=h,
            primary_color=config.brand.colors.primary,
            secondary_color=config.brand.colors.secondary,
            bg_color=config.brand.colors.background,
            t=0.0
        )
        _BG_CACHE[preset_cache_key] = bg
        return bg.copy()

    return render_background_preset(
        preset_name=preset_name,
        width=w,
        height=h,
        primary_color=config.brand.colors.primary,
        secondary_color=config.brand.colors.secondary,
        bg_color=config.brand.colors.background,
        t=t
    )

def get_typed_text(full_text: str, progress: float) -> str:
    if progress >= 1.0:
        return full_text
    num_chars = max(1, int(len(full_text) * max(0.0, progress)))
    return full_text[:num_chars]

def resolve_color(c: Any, config: ProjectConfig) -> Tuple[int, int, int]:
    if isinstance(c, (list, tuple)) and len(c) >= 3:
        return (int(c[0]), int(c[1]), int(c[2]))
    if isinstance(c, str):
        c_lower = c.lower().strip()
        color_map = {
            "primary": config.brand.colors.primary,
            "secondary": config.brand.colors.secondary,
            "accent": config.brand.colors.accent,
            "background": config.brand.colors.background,
            "text_primary": config.brand.colors.text_primary,
            "text_secondary": config.brand.colors.text_secondary,
            "danger": config.brand.colors.danger,
            "highlight": config.brand.colors.highlight,
        }
        if c_lower in color_map:
            return color_map[c_lower]
        if c_lower.startswith("#"):
            return hex_to_rgb(c_lower)
    return config.brand.colors.text_primary

def draw_pill(canvas: Image.Image, text: str, pos: Tuple[int, int], font_size: int = 38,
              bg_color=(12, 28, 52), border_color=(255, 138, 0), text_color=(255, 255, 255),
              project_dir: Optional[str] = None) -> Image.Image:
    font = get_font(font_size, project_dir)
    dummy = Image.new("RGBA", (1, 1))
    d_draw = ImageDraw.Draw(dummy)
    bbox = d_draw.textbbox((0, 0), text, font=font, direction="rtl")
    tw = (bbox[2] - bbox[0]) if bbox else 200
    th = font_size
    pw, ph = tw + 70, th + 36

    pill_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(pill_layer)
    cx, cy = pos
    left, top = cx - pw // 2, cy - ph // 2
    right, bottom = cx + pw // 2, cy + ph // 2

    # Drop shadow
    draw.rounded_rectangle((left + 4, top + 4, right + 4, bottom + 4), radius=ph // 2, fill=(0, 0, 0, 100))
    # Main pill
    draw.rounded_rectangle((left, top, right, bottom), radius=ph // 2, fill=bg_color + (240,), outline=border_color + (255,), width=3)
    # RTL text
    draw.text((cx, cy), text, fill=text_color + (255,), font=font, anchor="mm", direction="rtl")
    return Image.alpha_composite(canvas, pill_layer)

def draw_animated_icon(canvas: Image.Image, icon_el: IconElement, config: ProjectConfig, t: float, scene_start: float, scene_end: float) -> Image.Image:
    """Draws an animated 3D icon with elastic bounce, floating physics, or glitch shake."""
    if icon_el.start is not None and t < icon_el.start:
        return canvas
    if icon_el.end is not None and t > icon_el.end:
        return canvas

    time_in_icon = (t - icon_el.start) if icon_el.start is not None else (t - scene_start)
    if time_in_icon < 0:
        return canvas

    # Resolve icon path
    icon_path = icon_el.name
    named_icons = ["rocket", "warning", "wall", "clock", "lightning", "sad", "eyes", "chart", "money", "card", "gear", "package", "check", "cross", "fire", "brain", "laptop", "locked", "collision"]
    if icon_el.name in named_icons:
        cand = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons_3d", f"{icon_el.name}.png"))
        if os.path.exists(cand):
            icon_path = cand
    elif not os.path.isabs(icon_path):
        cand = os.path.join(config.project_dir, icon_path)
        if os.path.exists(cand):
            icon_path = cand

    img = load_cached_image(icon_path)
    if not img:
        return canvas

    target_size = icon_el.size
    scale = 1.0
    alpha = 1.0
    rotation = 0.0
    y_offset = 0
    x_offset = 0

    anim = getattr(icon_el, "animation", "pop_bounce") or "pop_bounce"
    if anim == "pop_bounce":
        if time_in_icon < 0.35:
            p = time_in_icon / 0.35
            # Elastic overshoot punch
            scale = math.sin(p * math.pi / 2) * (1.0 + 0.20 * math.exp(-p * 5.0) * math.sin(p * math.pi * 3))
            alpha = min(1.0, p * 2.0)
        else:
            scale = 1.0
            alpha = 1.0
            y_offset = int(math.sin(time_in_icon * 3.0) * 6)
    elif anim == "float":
        y_offset = int(math.sin(time_in_icon * 2.8) * 12)
        scale = 1.0
    elif anim == "shake":
        decay = math.exp(-time_in_icon * 2.5)
        x_offset = int(math.sin(time_in_icon * 35.0) * 12 * decay)
        y_offset = int(math.cos(time_in_icon * 28.0) * 6 * decay)
    elif anim == "rotate_pulse":
        rotation = math.sin(time_in_icon * 2.5) * 8.0
        scale = 1.0 + 0.04 * math.sin(time_in_icon * 4.0)

    cur_w = max(10, int(target_size * scale))
    cur_h = max(10, int(target_size * scale))

    icon_res = img.resize((cur_w, cur_h), Image.Resampling.LANCZOS)
    if rotation != 0.0:
        icon_res = icon_res.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=True)
        cur_w, cur_h = icon_res.size

    cx = icon_el.pos[0] + x_offset
    cy = icon_el.pos[1] + y_offset

    # Soft glowing neon aura behind the icon
    aura_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    a_draw = ImageDraw.Draw(aura_layer)
    aura_col = icon_el.label_color or config.brand.colors.primary
    aura_radius = int(target_size * 0.75 * scale)
    for r in range(aura_radius, 0, -15):
        ratio = 1.0 - (r / aura_radius)
        a_draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=aura_col + (int(ratio * 35 * alpha),))
    canvas = Image.alpha_composite(canvas, aura_layer)

    # Paste the 3D icon
    canvas.paste(icon_res, (cx - cur_w // 2, cy - cur_h // 2), icon_res)

    # Optional descriptive pill below icon
    if icon_el.label:
        canvas = draw_pill(
            canvas=canvas,
            text=icon_el.label,
            pos=(cx, cy + cur_h // 2 + 36),
            font_size=32,
            bg_color=(12, 16, 28),
            border_color=aura_col,
            text_color=(255, 255, 255),
            project_dir=config.project_dir
        )

    return canvas

def draw_code_card(canvas: Image.Image, code_el: CodeCardElement, config: ProjectConfig, t: float, scene_start: float, scene_end: float) -> Image.Image:
    """Draws a sleek macOS / VS Code dark code editor card with syntax highlighting and typing reveal."""
    if code_el.start is not None and t < code_el.start:
        return canvas
    if code_el.end is not None and t > code_el.end:
        return canvas

    time_in = (t - code_el.start) if code_el.start is not None else (t - scene_start)
    if time_in < 0:
        return canvas

    w = code_el.width
    lines = code_el.code_lines or []
    line_h = 42
    titlebar_h = 52
    pad_y = 26
    total_h = titlebar_h + pad_y * 2 + len(lines) * line_h

    # Card animation pop
    scale = 1.0
    alpha = 1.0
    if time_in < 0.3:
        p = time_in / 0.3
        scale = math.sin(p * math.pi / 2) * (1.0 + 0.06 * (1.0 - p))
        alpha = min(1.0, p * 2.0)

    cur_w = int(w * scale)
    cur_h = int(total_h * scale)
    cx, cy = code_el.pos
    x1, y1 = cx - cur_w // 2, cy - cur_h // 2
    x2, y2 = cx + cur_w // 2, cy + cur_h // 2

    card_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(card_layer)

    # Soft glowing border aura
    draw.rounded_rectangle((x1 - 4, y1 - 4, x2 + 4, y2 + 4), radius=24, fill=config.brand.colors.primary + (int(25 * alpha),))
    # Dark IDE body
    draw.rounded_rectangle((x1, y1, x2, y2), radius=20, fill=(13, 17, 24, int(245 * alpha)), outline=(48, 54, 61, int(220 * alpha)), width=2)
    # Title bar divider
    tb_bottom = y1 + int(titlebar_h * scale)
    draw.line([(x1, tb_bottom), (x2, tb_bottom)], fill=(33, 38, 45, int(240 * alpha)), width=2)

    # macOS window buttons
    dot_y = y1 + int(titlebar_h * scale // 2)
    dot_r = int(7 * scale)
    draw.ellipse((x1 + 24 - dot_r, dot_y - dot_r, x1 + 24 + dot_r, dot_y + dot_r), fill=(255, 95, 86, int(240 * alpha)))
    draw.ellipse((x1 + 48 - dot_r, dot_y - dot_r, x1 + 48 + dot_r, dot_y + dot_r), fill=(255, 189, 46, int(240 * alpha)))
    draw.ellipse((x1 + 72 - dot_r, dot_y - dot_r, x1 + 72 + dot_r, dot_y + dot_r), fill=(39, 201, 63, int(240 * alpha)))

    # Title text
    title_font = get_font(max(20, int(26 * scale)), config.project_dir)
    draw.text((cx, dot_y), code_el.title, fill=(160, 175, 195, int(220 * alpha)), font=title_font, anchor="mm")

    # Code lines with syntax highlighting
    code_font = get_font(max(18, int(28 * scale)), config.project_dir)
    start_code_y = tb_bottom + int(pad_y * scale)

    visible_lines = len(lines)
    if code_el.animation == "typewriter":
        visible_lines = min(len(lines), max(1, int(time_in * 3.5)))

    for i in range(visible_lines):
        line_str = lines[i]
        curr_line_y = start_code_y + int(i * line_h * scale)
        # Line number
        draw.text((x1 + int(24 * scale), curr_line_y), f"{i+1:2d}", fill=(80, 90, 105, int(180 * alpha)), font=code_font)

        # Highlight keywords
        col = (230, 237, 243, int(255 * alpha))
        if any(line_str.strip().startswith(kw) for kw in ["def ", "class ", "import ", "from ", "async ", "return"]):
            col = (255, 123, 114, int(255 * alpha))  # keyword salmon
        elif "=" in line_str or ":" in line_str:
            col = (121, 192, 255, int(255 * alpha))  # var cyan
        elif line_str.strip().startswith("#"):
            col = (139, 148, 158, int(200 * alpha))  # comment gray
        elif '"' in line_str or "'" in line_str:
            col = (126, 231, 138, int(255 * alpha))  # string green

        draw.text((x1 + int(85 * scale), curr_line_y), line_str, fill=col, font=code_font)

    return Image.alpha_composite(canvas, card_layer)

def draw_comparison(canvas: Image.Image, cmp_el: ComparisonElement, config: ProjectConfig, t: float, scene_start: float, scene_end: float) -> Image.Image:
    """Draws side-by-side comparison cards (e.g. Old 90s POS vs Modern Tazara UI)."""
    time_in = t - scene_start
    card_w = int((cmp_el.width - 40) // 2)
    card_h = 500
    cx, cy = cmp_el.pos

    left_x = cx - card_w // 2 - 20
    right_x = cx + card_w // 2 + 20

    p = min(1.0, time_in / 0.35)
    scale = math.sin(p * math.pi / 2)

    comp_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(comp_layer)

    # 1. Left Card: Old system (Red accent)
    lx1 = left_x - int(card_w * scale) // 2
    lx2 = left_x + int(card_w * scale) // 2
    ly1 = cy - int(card_h * scale) // 2
    ly2 = cy + int(card_h * scale) // 2
    draw.rounded_rectangle((lx1, ly1, lx2, ly2), radius=22, fill=(16, 12, 14, 235), outline=(255, 95, 86, 200), width=3)

    font_h = get_font(34, config.project_dir)
    draw.text((left_x, ly1 + 45), cmp_el.old_title, fill=(255, 120, 110), font=font_h, anchor="mm", direction="rtl")

    font_d = get_font(28, config.project_dir)
    if cmp_el.old_desc:
        draw.text((left_x, ly2 - 45), cmp_el.old_desc, fill=(180, 160, 160), font=font_d, anchor="mm", direction="rtl")

    # 2. Right Card: Tazara UI (Lime / Purple neon accent)
    rx1 = right_x - int(card_w * scale) // 2
    rx2 = right_x + int(card_w * scale) // 2
    ry1 = cy - int(card_h * scale) // 2
    ry2 = cy + int(card_h * scale) // 2
    draw.rounded_rectangle((rx1 - 2, ry1 - 2, rx2 + 2, ry2 + 2), radius=24, fill=config.brand.colors.secondary + (40,))
    draw.rounded_rectangle((rx1, ry1, rx2, ry2), radius=22, fill=(10, 16, 26, 240), outline=config.brand.colors.secondary + (255,), width=3)

    draw.text((right_x, ry1 + 45), cmp_el.new_title, fill=config.brand.colors.secondary, font=font_h, anchor="mm", direction="rtl")
    if cmp_el.new_desc:
        draw.text((right_x, ry2 - 45), cmp_el.new_desc, fill=(240, 245, 250), font=font_d, anchor="mm", direction="rtl")

    # Paste preview images if present
    if cmp_el.old_image and os.path.exists(cmp_el.old_image):
        old_img = load_cached_image(cmp_el.old_image)
        if old_img:
            mw = int(card_w * 0.82 * scale)
            mh = int(mw * 0.6)
            old_res = old_img.resize((mw, mh), Image.Resampling.LANCZOS)
            comp_layer.paste(old_res, (left_x - mw // 2, cy - mh // 2), old_res)

    if cmp_el.new_image and os.path.exists(cmp_el.new_image):
        new_img = load_cached_image(cmp_el.new_image)
        if new_img:
            mw = int(card_w * 0.82 * scale)
            mh = int(mw * 0.6)
            new_res = new_img.resize((mw, mh), Image.Resampling.LANCZOS)
            comp_layer.paste(new_res, (right_x - mw // 2, cy - mh // 2), new_res)

    return Image.alpha_composite(canvas, comp_layer)

def draw_badge_widget(canvas: Image.Image, badge_el: BadgeWidgetElement, config: ProjectConfig, t: float, scene_start: float, scene_end: float) -> Image.Image:
    """Draws a floating system status badge / notification widget."""
    if badge_el.start is not None and t < badge_el.start:
        return canvas
    if badge_el.end is not None and t > badge_el.end:
        return canvas

    time_in = (t - badge_el.start) if badge_el.start is not None else (t - scene_start)
    if time_in < 0:
        return canvas

    status_colors = {
        "success": ((16, 185, 129), (5, 150, 105)),
        "danger": ((239, 68, 68), (220, 38, 38)),
        "warning": ((245, 158, 11), (217, 119, 6)),
        "info": ((59, 130, 246), (37, 99, 235))
    }
    bg_tint, border_col = status_colors.get(badge_el.status, status_colors["success"])

    p = min(1.0, time_in / 0.28)
    y_offset = int((1.0 - math.sin(p * math.pi / 2)) * -40)
    alpha = min(1.0, p * 2.0)

    disp_text = badge_el.text
    font = get_font(34, config.project_dir)

    dummy = Image.new("RGBA", (1, 1))
    d_draw = ImageDraw.Draw(dummy)
    bbox = d_draw.textbbox((0, 0), disp_text, font=font, direction="rtl")
    tw = (bbox[2] - bbox[0]) if bbox else 240
    pw, ph = tw + 85, 68

    cx, cy = badge_el.pos[0], badge_el.pos[1] + y_offset
    bx1, by1 = cx - pw // 2, cy - ph // 2
    bx2, by2 = cx + pw // 2, cy + ph // 2

    b_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(b_layer)
    draw.rounded_rectangle((bx1 - 2, by1 - 2, bx2 + 2, by2 + 2), radius=ph // 2, fill=border_col + (int(35 * alpha),))
    draw.rounded_rectangle((bx1, by1, bx2, by2), radius=ph // 2, fill=(12, 18, 30, int(240 * alpha)), outline=border_col + (int(220 * alpha),), width=2)

    # Glowing LED status dot on right side for RTL
    dot_x = bx2 - 32
    draw.ellipse((dot_x - 12, cy - 12, dot_x + 12, cy + 12), fill=border_col + (int(70 * alpha),))
    draw.ellipse((dot_x - 6, cy - 6, dot_x + 6, cy + 6), fill=border_col + (int(255 * alpha),))

    # Text offset slightly to left of LED dot
    text_cx = cx - 14
    draw.text((text_cx, cy), disp_text, fill=(255, 255, 255, int(255 * alpha)), font=font, anchor="mm", direction="rtl")

    return Image.alpha_composite(canvas, b_layer)

def render_scene(canvas: Image.Image, scene: SceneConfig, config: ProjectConfig, t: float) -> Image.Image:
    duration = max(0.01, scene.end - scene.start)
    rel_t = (t - scene.start) / duration
    draw = ImageDraw.Draw(canvas)

    from .typography import draw_animated_text

    # 1. Standard Texts with Optical Vertical & Horizontal Auto-Centering & Progressive Reveal
    if scene.texts and scene.scene_type != "cta":
        num_texts = len(scene.texts)
        # Pre-calculate exact heights of each text element using the font to avoid overlap
        elem_heights = []
        elem_fonts = []
        from .typography import auto_fit_text, get_text_size
        min_f = 50 if (scene.mockup and scene.mockup.image_path) else 66
        for text_el in scene.texts:
            f_size = max(text_el.size, min_f)
            f_obj, wrapped_lines = auto_fit_text(text_el.text, lambda s: get_font(s, config.project_dir), initial_size=f_size, max_width=920)
            _, l_h = get_text_size("تجربة", f_obj)
            block_h = len(wrapped_lines) * (l_h + 20)
            elem_heights.append(block_h)

        gap = 32 if (scene.mockup and scene.mockup.image_path) else 48
        total_layout_h = sum(elem_heights) + (max(0, num_texts - 1) * gap)
        if scene.mockup and scene.mockup.image_path:
            # Estimate actual top of mockup card: y - (ph // 2) - 35
            # Default ratio ~ 0.55
            approx_ph = int(scene.mockup.width * 0.55)
            mockup_card_top = scene.mockup.y - (approx_ph // 2) - 35
            # Available space between header (y=210) and mockup card top with 30px buffer
            avail_h = max(200, (mockup_card_top - 30) - 210)
            center_y_start = 210 + max(0, int((avail_h - total_layout_h) // 2))
        else:
            center_y_start = 960 - (total_layout_h // 2)

        # Count words per text element to distribute progress proportionately
        elem_word_counts = [max(1, len(el.text.split())) for el in scene.texts]
        total_words_scene = sum(elem_word_counts)

        accum_words = 0
        current_y = center_y_start
        for idx, text_el in enumerate(scene.texts):
            w_count = elem_word_counts[idx]
            block_h = elem_heights[idx]
            computed_y = current_y + (block_h // 2)
            current_y += block_h + gap

            # Time window for this specific phrase/line within the scene
            if hasattr(text_el, "start") and text_el.start is not None and hasattr(text_el, "end") and text_el.end is not None:
                # Absolute millisecond-accurate timing directly synchronized with voiceover
                if t < text_el.start:
                    # Don't show future lines yet (clean focus on current speech)
                    continue
                phrase_progress = min(1.0, max(0.0, (t - text_el.start) / max(0.001, (text_el.end - text_el.start))))
                is_past_phrase = (t >= text_el.end)
            else:
                seg_start = accum_words / total_words_scene
                seg_end = (accum_words + w_count) / total_words_scene
                accum_words += w_count

                # Progress of current phrase: 0 before start, 0->1 during its speech window, 1 after
                if rel_t < seg_start:
                    # Don't show future lines yet (clean focus on current speech)
                    continue

                phrase_progress = min(1.0, max(0.0, (rel_t - seg_start) / max(0.001, (seg_end - seg_start))))
                is_past_phrase = (rel_t >= seg_end)

            color_rgb = resolve_color(text_el.color, config)
            font_size = max(text_el.size, min_f)

            if is_past_phrase:
                # Finished spoken phrase: show all words in clean crisp white with drop shadow
                canvas = draw_animated_text(
                    canvas=canvas,
                    text=text_el.text,
                    pos=(config.width // 2, computed_y),
                    font_fn=lambda s: get_font(s, config.project_dir),
                    size=font_size,
                    color=(255, 255, 255),
                    highlight_color=(255, 255, 255),
                    animation="static",
                    progress=1.0
                )
            else:
                # Actively spoken phrase: highlight current spoken word in fluorescent lime
                canvas = draw_animated_text(
                    canvas=canvas,
                    text=text_el.text,
                    pos=(config.width // 2, computed_y),
                    font_fn=lambda s: get_font(s, config.project_dir),
                    size=font_size,
                    color=color_rgb,
                    highlight_color=config.brand.colors.highlight,
                    animation=text_el.animation or "word_pop",
                    progress=phrase_progress
                )

    # 2. Pills
    for pill in scene.pills:
        canvas = draw_pill(
            canvas,
            text=pill.text,
            pos=pill.pos,
            font_size=pill.font_size,
            bg_color=pill.bg_color or config.brand.colors.secondary,
            border_color=pill.border_color or config.brand.colors.primary,
            text_color=pill.text_color,
            project_dir=config.project_dir
        )

    # 3. Mockup image / Central Logo / System UI Presentation with Dynamic Animation
    if scene.mockup and (scene.mockup.image_path or (hasattr(scene.mockup, "images") and scene.mockup.images)):
        time_in_scene = max(0.0, t - scene.start)
        anim_type = getattr(scene.mockup, "animate", "pop_in") or "pop_in"
        images_list = getattr(scene.mockup, "images", None)

        # 3a. Rapid filmstrip image sequence switching if anim_type == "filmstrip_fast"
        active_img_path = scene.mockup.image_path
        if anim_type == "filmstrip_fast" and images_list and len(images_list) > 0:
            # Switch screenshot every 0.38 seconds with a smooth punch
            switch_rate = 0.38
            img_idx = int(time_in_scene / switch_rate) % len(images_list)
            active_img_path = images_list[img_idx]
        elif anim_type in ("video", "video_loop") and images_list and len(images_list) > 0:
            # Smooth 30fps playback of extracted frames
            frame_idx = int(time_in_scene * 30.0) % len(images_list)
            active_img_path = images_list[frame_idx]

        mock_img = load_cached_image(active_img_path)
        if mock_img:
            pw = scene.mockup.width
            ratio = (mock_img.height / mock_img.width) if mock_img.width > 0 else (693 / 335)
            ph = int(pw * ratio)

            scale_anim = 1.0
            alpha_anim = 1.0
            y_offset = 0

            if anim_type == "filmstrip_fast":
                # Rapid pop on each photo switch
                sub_t = (time_in_scene % 0.38) / 0.38
                if sub_t < 0.20:
                    punch = sub_t / 0.20
                    scale_anim = 1.0 + 0.05 * math.sin(punch * math.pi)
                else:
                    scale_anim = 1.0
                alpha_anim = 1.0
            elif anim_type == "pop_in":
                if time_in_scene < 0.35:
                    p = time_in_scene / 0.35
                    scale_anim = math.sin(p * math.pi / 2) * (1.0 + 0.08 * (1.0 - p))
                    alpha_anim = min(1.0, p * 1.5)
                else:
                    scale_anim = 1.0
                    alpha_anim = 1.0
            elif anim_type == "float":
                y_offset = int(math.sin(time_in_scene * 2.5) * 8.0)

            cur_w = max(10, int(pw * scale_anim))
            cur_h = max(10, int(ph * scale_anim))

            mock_res = mock_img.resize((cur_w, cur_h), Image.Resampling.LANCZOS)
            if alpha_anim < 1.0:
                r, g, b, a = mock_res.split()
                a_arr = np.array(a, dtype=np.float32) * alpha_anim
                mock_res = Image.merge("RGBA", (r, g, b, Image.fromarray(a_arr.astype(np.uint8))))

            cx = config.width // 2
            cy = scene.mockup.y + y_offset

            # 3b. Radial Focus Blur / Dramatic Vignette Spotlight around images if blur_bg is True
            if getattr(scene.mockup, "blur_bg", False) or anim_type == "filmstrip_fast":
                # Create a cinematic dark radial vignette around the center to focus the eye
                vig_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
                v_draw = ImageDraw.Draw(vig_layer)
                # Soft dark vignette focusing on the screenshot
                for r_step in range(max(cur_w, cur_h) + 320, max(cur_w, cur_h) - 40, -40):
                    v_alpha = int((1.0 - (r_step - max(cur_w, cur_h) + 40) / 360.0) * 160)
                    v_draw.ellipse((cx - r_step, cy - r_step // 2, cx + r_step, cy + r_step // 2), fill=(0, 0, 0, max(0, v_alpha)))
                canvas = Image.alpha_composite(canvas, vig_layer)

            # Optional sleek frosted glass card with glowing fluorescent border
            use_card = getattr(scene.mockup, "card", True)
            if use_card:
                pad_x = int(35 * scale_anim)
                pad_y = int(25 * scale_anim)
                bx1 = cx - cur_w // 2 - pad_x
                by1 = cy - cur_h // 2 - pad_y
                bx2 = cx + cur_w // 2 + pad_x
                by2 = cy + cur_h // 2 + pad_y

                card_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
                c_draw = ImageDraw.Draw(card_layer)
                card_alpha = int(alpha_anim * 255)
                # Soft neon aura
                c_draw.rounded_rectangle((bx1 - 4, by1 - 4, bx2 + 4, by2 + 4), radius=28, fill=config.brand.colors.primary + (int(35 * alpha_anim),))
                # Deep glass card
                c_draw.rounded_rectangle((bx1, by1, bx2, by2), radius=24, fill=(10, 14, 24, int(235 * alpha_anim)), outline=config.brand.colors.primary + (int(220 * alpha_anim),), width=3)
                canvas = Image.alpha_composite(canvas, card_layer)

            # Paste mockup
            canvas.paste(mock_res, (cx - cur_w // 2, cy - cur_h // 2), mock_res)

    # 3b. Animated 3D Icons
    for icon_el in getattr(scene, "icons", []):
        canvas = draw_animated_icon(canvas, icon_el, config, t, scene.start, scene.end)

    # 3c. Code Editor Card
    if getattr(scene, "code_card", None):
        canvas = draw_code_card(canvas, scene.code_card, config, t, scene.start, scene.end)

    # 3d. Comparison Side-by-Side Card
    if getattr(scene, "comparison", None):
        canvas = draw_comparison(canvas, scene.comparison, config, t, scene.start, scene.end)

    # 3e. Floating Badges / Status Widgets
    for badge_el in getattr(scene, "badges", []):
        canvas = draw_badge_widget(canvas, badge_el, config, t, scene.start, scene.end)

    # 4. CTA Scene Extras (Solid Black Screen with Digital Countdown Counter: "استنى Part 2 من الرحلة")
    if scene.scene_type == "cta":
        # Cover whole background with deep pitch black as requested
        canvas = Image.new("RGBA", canvas.size, (0, 0, 0, 255))
        draw = ImageDraw.Draw(canvas)

        # 1. Top Mini Pill: انتظروا المفاجأة الكبرى
        canvas = draw_pill(
            canvas,
            text="انتظروا المفاجأة الكبرى",
            pos=(config.width // 2, 720),
            font_size=36,
            bg_color=(12, 16, 28),
            border_color=config.brand.colors.secondary,
            text_color=(255, 255, 255),
            project_dir=config.project_dir
        )
        draw = ImageDraw.Draw(canvas)

        # 2. Glowing Digital Counter Box
        clock_box_y = 860
        cb_w, cb_h = 460, 96
        cb_x1, cb_x2 = (config.width - cb_w) // 2, (config.width + cb_w) // 2
        draw.rounded_rectangle((cb_x1, clock_box_y - cb_h // 2, cb_x2, clock_box_y + cb_h // 2), radius=24, fill=(6, 8, 16, 255), outline=config.brand.colors.secondary + (255,), width=3)

        reel_num = getattr(config, "reel_number", "") or "فيديو 01"
        if "01" in reel_num or "1" in reel_num:
            part_str = "[ PART • 02 ]"
            callout_str = "استنى Part 2 من الرحلة"
            sub_str = "تابع الحساب عشان تشوف تفاصيل الخناقة والهوية"
        elif "02" in reel_num or "2" in reel_num:
            part_str = "[ PART • 03 ]"
            callout_str = "استنى Part 3 من الرحلة"
            sub_str = "تابع الحساب عشان تشوف معمارية الكود والسيستم!"
        elif "03" in reel_num or "3" in reel_num:
            part_str = "[ PART • 04 ]"
            callout_str = "استنى Part 4 من الرحلة"
            sub_str = "تابع الحساب عشان تشوف الكود والتحدي!"
        elif "04" in reel_num or "4" in reel_num:
            part_str = "[ PART • 05 ]"
            callout_str = "استنى Part 5 من الرحلة"
            sub_str = "تابع الحساب عشان تشوف شكل السيستم وتجربته!"
        elif "05" in reel_num or "5" in reel_num:
            part_str = "[ PART • 06 ]"
            callout_str = "استنى Part 6 من الرحلة"
            sub_str = "تابع الحساب عشان تشوف نزول السيستم لأول محل!"
        else:
            part_str = "[ PART • NEXT ]"
            callout_str = "استنى الجزء القادم من الرحلة"
            sub_str = "تابع الحساب لمتابعة باقي القصة والتفاصيل!"

        clock_font = get_font(52, config.project_dir)
        draw.text((config.width // 2, clock_box_y), part_str, fill=config.brand.colors.secondary + (255,), font=clock_font, direction="rtl", anchor="mm")

        # 3. Main Callout Heading
        heading_font = get_font(74, config.project_dir)
        draw.text((config.width // 2 + 4, 1025 + 4), callout_str, fill=(0, 0, 0, 240), font=heading_font, direction="rtl", anchor="mm")
        draw.text((config.width // 2, 1025), callout_str, fill=(255, 255, 255, 255), font=heading_font, direction="rtl", anchor="mm")

        # 4. Teaser Subtext
        sub_font = get_font(42, config.project_dir)
        draw.text((config.width // 2, 1135), sub_str, fill=(226, 232, 240, 255), font=sub_font, direction="rtl", anchor="mm")

    # 5. Scene Transition Visual FX (Cinematic, Modern & Clean)
    trans = getattr(scene, "transition", "none") or "none"
    time_in_scene = t - scene.start
    if trans == "flash_white" and time_in_scene < 0.22:
        # Soft cinematic bloom flash
        p_flash = 1.0 - (time_in_scene / 0.22)
        flash_alpha = int(math.pow(p_flash, 2) * 160)
        flash_layer = Image.new("RGBA", canvas.size, (255, 255, 255, flash_alpha))
        canvas = Image.alpha_composite(canvas, flash_layer)
    elif trans == "fade_black" and time_in_scene < 0.25:
        p_fade = 1.0 - (time_in_scene / 0.25)
        black_alpha = int(p_fade * 220)
        black_layer = Image.new("RGBA", canvas.size, (0, 0, 0, black_alpha))
        canvas = Image.alpha_composite(canvas, black_layer)
    elif trans in ("zoom_in_cut", "zoom_punch") and time_in_scene < 0.32:
        # Smooth camera punch-in that settles gently
        p_trans = time_in_scene / 0.32
        ease_p = 1.0 - math.pow(1.0 - p_trans, 3)
        scale_punch = 1.0 + 0.06 * (1.0 - ease_p)
        w, h = canvas.size
        sw, sh = int(w * scale_punch), int(h * scale_punch)
        res = canvas.resize((sw, sh), Image.Resampling.BILINEAR)
        ox = (w - sw) // 2
        oy = (h - sh) // 2
        canvas = res.crop((-ox, -oy, w - ox, h - oy))

    return canvas

def apply_chromatic_aberration(img: Image.Image, offset: int) -> Image.Image:
    """Splits RGB channels horizontally for a glitch / chromatic distortion effect."""
    if offset == 0:
        return img
    r, g, b, a = img.split()
    r_arr = np.array(r)
    b_arr = np.array(b)
    r_arr = np.roll(r_arr, offset, axis=1)
    b_arr = np.roll(b_arr, -offset, axis=1)
    if offset > 0:
        r_arr[:, :offset] = 0
        b_arr[:, -offset:] = 0
    else:
        r_arr[:, offset:] = 0
        b_arr[:, :-offset:] = 0
    return Image.merge("RGBA", (Image.fromarray(r_arr), g, Image.fromarray(b_arr), a))

def render_frame_by_config(config: ProjectConfig, frame_idx: int) -> Image.Image:
    """Renders a single frame at frame_idx for any brand/project configuration."""
    t = frame_idx / config.fps

    # 1. Find active scene with strict non-overlapping intervals
    active_scene = None
    for i, scene in enumerate(config.scenes):
        is_last = (i == len(config.scenes) - 1)
        if is_last:
            if scene.start <= t <= (scene.end + 0.1):
                active_scene = scene
                break
        else:
            if scene.start <= t < scene.end:
                active_scene = scene
                break

    if active_scene is None and len(config.scenes) > 0:
        if t >= config.scenes[-1].end:
            active_scene = config.scenes[-1]
        else:
            active_scene = config.scenes[0]

    # Resolve background preset with optional per-scene bg_motion
    bg_override = getattr(active_scene, "bg_motion", None) if active_scene else None
    canvas = get_base_background(config, t, preset_override=bg_override)

    if active_scene:
        w, h = canvas.size
        is_hook = (active_scene.id == "scene_01" and t < 0.85)

        if is_hook:
            # Render foreground onto transparent layer to preserve rock-solid static background
            scene_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            scene_layer = render_scene(scene_layer, active_scene, config, t)

            # Anamorphic flare burst directly behind hook text
            if t < 0.35:
                flare_p = 1.0 - (t / 0.35)
                flare_alpha = int((flare_p ** 2) * 180)
                flare_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                f_draw = ImageDraw.Draw(flare_layer)
                cy = 710  # Centered with hook text
                primary_col = config.brand.colors.primary

                # Soft glowing bloom
                for r in range(180, 0, -20):
                    b_alpha = int((1.0 - r / 180.0) * flare_alpha * 0.4)
                    f_draw.ellipse((w // 2 - r, cy - r // 2, w // 2 + r, cy + r // 2), fill=primary_col + (b_alpha,))

                # Horizontal glowing streak
                f_draw.line([(w // 2 - 450, cy), (w // 2 + 450, cy)], fill=primary_col + (flare_alpha,), width=6)
                f_draw.line([(w // 2 - 250, cy), (w // 2 + 250, cy)], fill=(255, 255, 255, int(flare_alpha * 0.95)), width=2)
                canvas = Image.alpha_composite(canvas, flare_layer)

            # Chromatic aberration RGB glitch on the hook text
            decay = math.exp(-t * 6.5)
            glitch_decay = math.exp(-t * 8.0)
            split_offset = int(math.sin(t * 45.0) * 14.0 * glitch_decay)

            if abs(split_offset) >= 1:
                scene_layer = apply_chromatic_aberration(scene_layer, split_offset)

            # Dynamic scale punch on the hook text
            if t < 0.55:
                scale_punch = 1.0 + 0.06 * decay
                sw, sh = int(w * scale_punch), int(h * scale_punch)
                res = scene_layer.resize((sw, sh), Image.Resampling.BILINEAR)
                ox = (w - sw) // 2
                oy = (h - sh) // 2
                scene_layer = res.crop((-ox, -oy, w - ox, h - oy))

        else:
            # Render foreground onto transparent layer so background grid remains 100% static with zero flicker
            scene_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            scene_layer = render_scene(scene_layer, active_scene, config, t)

            # Advanced After Effects Virtual Camera Engine (Push-in, Whip-Pan, Dutch Tilt, 3D Orbit, Motion Blur)
            if active_scene.scene_type != "cta":
                try:
                    from .ae_camera import AECameraEngine
                except ImportError:
                    try:
                        from ae_camera import AECameraEngine
                    except ImportError:
                        AECameraEngine = None

                dur = max(0.01, active_scene.end - active_scene.start)
                t_in_scene = max(0.0, t - active_scene.start)

                if AECameraEngine:
                    scene_meta = {
                        "camera": getattr(active_scene, "camera", {
                            "type": getattr(active_scene, "camera_motion", "push_in"),
                            "intensity": float(getattr(active_scene, "camera_intensity", 1.0)),
                            "handheld": True,
                            "shake": getattr(active_scene, "screen_shake", None)
                        })
                    }
                    cam_state = AECameraEngine.evaluate_camera(scene_meta, t_in_scene, dur)
                    scene_layer = AECameraEngine.apply_camera_to_canvas(scene_layer, cam_state)
                elif getattr(active_scene, "camera_drift", True):
                    drift_p = min(1.0, max(0.0, t_in_scene / dur))
                    d_scale = 1.0 + 0.024 * drift_p
                    sw, sh = int(w * d_scale), int(h * d_scale)
                    res = scene_layer.resize((sw, sh), Image.Resampling.BILINEAR)
                    ox = (w - sw) // 2
                    oy = (h - sh) // 2
                    scene_layer = res.crop((-ox, -oy, w - ox, h - oy))

            canvas = Image.alpha_composite(canvas, scene_layer)

        # Dynamic screen shake on high impact SFX or triggers
        shake_cfg = getattr(active_scene, "screen_shake", None)
        if shake_cfg and isinstance(shake_cfg, dict):
            shake_start = float(shake_cfg.get("start", active_scene.start))
            shake_dur = float(shake_cfg.get("duration", 0.35))
            if shake_start <= t <= (shake_start + shake_dur):
                time_in_shake = t - shake_start
                decay = 1.0 - (time_in_shake / shake_dur)
                intensity = float(shake_cfg.get("intensity", 14))
                off_x = int(math.sin(time_in_shake * 55.0) * intensity * decay)
                off_y = int(math.cos(time_in_shake * 42.0) * (intensity * 0.7) * decay)
                shook = Image.new("RGBA", (w, h), (0, 0, 0, 255))
                shook.paste(canvas, (off_x, off_y))
                canvas = shook

    # 2. Top Header Overlays (Always rendered on top from frame 0 to end)
    # 2a. Brand Logo (Cropped & Framed in Glassmorphism Badge)
    logo_drawn = False
    if config.brand.logo_path and os.path.exists(config.brand.logo_path):
        logo = load_cached_image(config.brand.logo_path)
        if logo:
            lw, lh = logo.size
            max_w, max_h = 280, 105
            scale = min(max_w / max(1, lw), max_h / max(1, lh))
            nw, nh = max(1, int(lw * scale)), max(1, int(lh * scale))
            logo_res = logo.resize((nw, nh), Image.Resampling.LANCZOS)
            if logo_res.mode != "RGBA":
                logo_res = logo_res.convert("RGBA")

            # Sleek modern frosted glass pill behind logo
            card_pad_x = 22
            card_pad_y = 12
            bx1 = 80 - card_pad_x
            by1 = 70 - card_pad_y
            bx2 = 80 + nw + card_pad_x
            by2 = 70 + nh + card_pad_y

            glass = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            g_draw = ImageDraw.Draw(glass)
            g_draw.rounded_rectangle((bx1, by1, bx2, by2), radius=22, fill=(10, 15, 28, 210), outline=config.brand.colors.primary + (190,), width=2)
            canvas = Image.alpha_composite(canvas, glass)

            canvas.paste(logo_res, (80, 70), logo_res)
            logo_drawn = True

    if not logo_drawn and config.brand.name:
        # Fallback sleek brand pill
        canvas = draw_pill(
            canvas,
            text=config.brand.name,
            pos=(180, 110),
            font_size=32,
            bg_color=(15, 23, 42),
            border_color=config.brand.colors.primary,
            text_color=(255, 255, 255),
            project_dir=config.project_dir
        )

    # 2b. Top Video / Reel Number Badge (e.g. "فيديو 01")
    if config.reel_number:
        canvas = draw_pill(
            canvas,
            text=config.reel_number,
            pos=(config.width - 160, 110),
            font_size=32,
            bg_color=(15, 23, 42),
            border_color=config.brand.colors.accent,
            text_color=(255, 255, 255),
            project_dir=config.project_dir
        )

    return canvas

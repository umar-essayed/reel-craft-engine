import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

def hex_to_rgb(hex_str: str, default: Tuple[int, int, int] = (255, 255, 255)) -> Tuple[int, int, int]:
    if not hex_str or not isinstance(hex_str, str):
        return default
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join([c * 2 for c in hex_clean])
    if len(hex_clean) != 6:
        return default
    try:
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        return (r, g, b)
    except ValueError:
        return default

@dataclass
class BrandColors:
    primary: Tuple[int, int, int] = (255, 138, 0)      # Amber / Accent
    secondary: Tuple[int, int, int] = (1, 67, 163)     # Deep Blue
    accent: Tuple[int, int, int] = (0, 210, 255)       # Cyan
    background: Tuple[int, int, int] = (8, 20, 38)     # Deep Navy
    text_primary: Tuple[int, int, int] = (255, 255, 255)
    text_secondary: Tuple[int, int, int] = (245, 245, 245)
    danger: Tuple[int, int, int] = (255, 95, 86)
    highlight: Tuple[int, int, int] = (255, 189, 46)

@dataclass
class BrandConfig:
    name: str = "My Brand"
    tagline: str = ""
    website: str = "brand.com"
    search_query: str = "Brand Name"
    cta_text: str = "اشترك الآن"
    logo_path: Optional[str] = None
    colors: BrandColors = field(default_factory=BrandColors)

@dataclass
class TextElement:
    text: str
    y: int
    size: int = 64
    color: Any = "text_primary" # Can be hex string, tuple, or key from BrandColors
    animation: str = "typewriter" # "typewriter", "fade_in", "static"
    speed: float = 1.5
    delay: float = 0.0
    start: Optional[float] = None
    end: Optional[float] = None

@dataclass
class PillElement:
    text: str
    pos: Tuple[int, int]
    font_size: int = 38
    bg_color: Optional[Tuple[int, int, int]] = None
    border_color: Optional[Tuple[int, int, int]] = None
    text_color: Tuple[int, int, int] = (255, 255, 255)

@dataclass
class MockupElement:
    image_path: str
    y: int = 1340
    width: int = 430
    aspect_ratio: Optional[float] = None
    animate: Optional[str] = "pop_in"  # "pop_in", "float", "static", "filmstrip_fast"
    card: bool = True
    images: Optional[List[str]] = None
    blur_bg: bool = False

@dataclass
class IconElement:
    name: str  # Icon name ("rocket", "warning", "wall", "clock", "lightning", "sad", "eyes", "chart", "money", etc.) or relative/abs file path
    pos: Tuple[int, int] = (540, 1380)
    size: int = 160
    animation: str = "pop_bounce"  # "pop_bounce", "float", "shake", "rotate_pulse", "static"
    start: Optional[float] = None
    end: Optional[float] = None
    label: Optional[str] = None
    label_color: Optional[Tuple[int, int, int]] = None

@dataclass
class CodeCardElement:
    title: str = "tazara_core.py"
    code_lines: List[str] = field(default_factory=list)
    pos: Tuple[int, int] = (540, 1380)
    width: int = 860
    language: str = "python"
    animation: str = "typewriter"  # "typewriter", "pop_in"
    start: Optional[float] = None
    end: Optional[float] = None

@dataclass
class ComparisonElement:
    old_title: str = "الأنظمة القديمة ❌"
    new_title: str = "واجهة تازارا ✅"
    old_image: Optional[str] = None
    new_image: Optional[str] = None
    old_desc: Optional[str] = "كئيبة وبطيئة"
    new_desc: Optional[str] = "عصرية وسريعة"
    pos: Tuple[int, int] = (540, 1360)
    width: int = 920
    animation: str = "pop_split"

@dataclass
class BadgeWidgetElement:
    text: str
    status: str = "success"  # "success", "danger", "warning", "info"
    icon: Optional[str] = None
    pos: Tuple[int, int] = (540, 420)
    animation: str = "slide_down"
    start: Optional[float] = None
    end: Optional[float] = None

@dataclass
class SceneConfig:
    id: str
    start: float
    end: float
    scene_type: str = "standard" # "standard", "cta", "custom"
    texts: List[TextElement] = field(default_factory=list)
    pills: List[PillElement] = field(default_factory=list)
    mockup: Optional[MockupElement] = None
    icons: List[IconElement] = field(default_factory=list)
    code_card: Optional[CodeCardElement] = None
    comparison: Optional[ComparisonElement] = None
    badges: List[BadgeWidgetElement] = field(default_factory=list)
    custom_bg: Optional[str] = None
    transition: Optional[str] = "none" # "none", "flash_white", "zoom_in_cut", "fade_black", "zoom_punch"
    camera_drift: bool = True
    screen_shake: Optional[Dict[str, Any]] = None
    bg_motion: Optional[str] = None # "ambient_particles", "code_stream"

@dataclass
class AudioConfig:
    voiceover_path: Optional[str] = None
    hook_boost_db: float = 3.5
    hook_duration: float = 3.0
    sfx_cues: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ProjectConfig:
    project_dir: str
    title: str = "Generic Reel"
    width: int = 1080
    height: int = 1920
    fps: int = 30
    total_duration: float = 14.0
    brand: BrandConfig = field(default_factory=BrandConfig)
    reel_number: Optional[str] = None
    audio: AudioConfig = field(default_factory=AudioConfig)
    scenes: List[SceneConfig] = field(default_factory=list)
    background_image: Optional[str] = None
    background_preset: Optional[str] = "cyber_grid"

    @property
    def total_frames(self) -> int:
        return int(round(self.total_duration * self.fps))

def load_project_config(project_path: str) -> ProjectConfig:
    """Loads and resolves a brand/reel project configuration from JSON or directory."""
    project_dir = os.path.abspath(project_path)
    if os.path.isfile(project_dir):
        config_file = project_dir
        project_dir = os.path.dirname(project_dir)
    else:
        candidates = ["project.json", "brand_reel.json", "config/timeline.json", "timeline.json"]
        config_file = None
        for cand in candidates:
            p = os.path.join(project_dir, cand)
            if os.path.exists(p):
                config_file = p
                break
        if not config_file:
            config_file = os.path.join(project_dir, "project.json")

    raw: Dict[str, Any] = {}
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            raw = json.load(f)

    # 1. Video Settings
    width = raw.get("width", raw.get("settings", {}).get("width", 1080))
    height = raw.get("height", raw.get("settings", {}).get("height", 1920))
    fps = raw.get("fps", raw.get("settings", {}).get("fps", 30))
    total_dur = raw.get("total_duration", raw.get("settings", {}).get("total_duration", 14.0))

    # 2. Brand Settings
    b_raw = raw.get("brand", {})
    c_raw = b_raw.get("colors", {})
    brand_colors = BrandColors(
        primary=hex_to_rgb(c_raw.get("primary"), (255, 138, 0)),
        secondary=hex_to_rgb(c_raw.get("secondary"), (1, 67, 163)),
        accent=hex_to_rgb(c_raw.get("accent"), (0, 210, 255)),
        background=hex_to_rgb(c_raw.get("background"), (8, 20, 38)),
        text_primary=hex_to_rgb(c_raw.get("text_primary"), (255, 255, 255)),
        text_secondary=hex_to_rgb(c_raw.get("text_secondary"), (245, 245, 245)),
        danger=hex_to_rgb(c_raw.get("danger"), (255, 95, 86)),
        highlight=hex_to_rgb(c_raw.get("highlight"), (255, 189, 46)),
    )

    logo_val = b_raw.get("logo", b_raw.get("logo_path"))
    resolved_logo = None
    if logo_val:
        resolved_logo = os.path.join(project_dir, logo_val) if not os.path.isabs(logo_val) else logo_val
    else:
        # Check standard paths
        for std in ["assets/logo.png", "logo.png", "assets/logo-zorar.png"]:
            sp = os.path.join(project_dir, std)
            if os.path.exists(sp):
                resolved_logo = sp
                break

    brand = BrandConfig(
        name=b_raw.get("name", "Brand"),
        tagline=b_raw.get("tagline", ""),
        website=b_raw.get("website", "brand.com"),
        search_query=b_raw.get("search_query", b_raw.get("name", "Brand")),
        cta_text=b_raw.get("cta_text", "اشترك الآن"),
        logo_path=resolved_logo,
        colors=brand_colors
    )

    # 3. Audio Settings
    a_raw = raw.get("audio", {})
    vo_path = a_raw.get("voiceover", a_raw.get("voiceover_path"))
    resolved_vo = None
    if vo_path:
        resolved_vo = os.path.join(project_dir, vo_path) if not os.path.isabs(vo_path) else vo_path
    else:
        for std_vo in ["audio/voiceover.mp3", "audio/input_voiceover.mp3", "audio/voiceover.wav"]:
            vp = os.path.join(project_dir, std_vo)
            if os.path.exists(vp):
                resolved_vo = vp
                break

    audio = AudioConfig(
        voiceover_path=resolved_vo,
        hook_boost_db=a_raw.get("hook_boost_db", 3.5),
        hook_duration=a_raw.get("hook_duration", 3.0),
        sfx_cues=a_raw.get("sfx", a_raw.get("sfx_cues", []))
    )

    # 4. Scenes Settings
    raw_scenes = raw.get("scenes", [])
    raw_scenes_parsed = []
    seen_ids = set()

    for sc in raw_scenes:
        sc_id = str(sc.get("id", len(raw_scenes_parsed) + 1))
        if sc_id in seen_ids:
            continue
        seen_ids.add(sc_id)

        texts = []
        for t in sc.get("texts", []):
            raw_y = float(t.get("y", 500))
            # If normalized fractional coordinate (e.g. 0.25), scale to 1920px height
            calc_y = int(raw_y * 1920) if (0.0 < raw_y <= 1.0) else int(raw_y)

            raw_size = float(t.get("size", 64))
            calc_size = int(raw_size * 200) if (0.0 < raw_size <= 1.0) else int(raw_size)

            texts.append(TextElement(
                text=t.get("text", ""),
                y=calc_y,
                size=max(24, calc_size),
                color=t.get("color", "text_primary"),
                animation=t.get("animation", "typewriter"),
                speed=t.get("speed", 1.5),
                delay=t.get("delay", 0.0),
                start=float(t["start"]) if ("start" in t and t["start"] is not None) else None,
                end=float(t["end"]) if ("end" in t and t["end"] is not None) else None
            ))

        pills = []
        for p in sc.get("pills", []):
            bg = hex_to_rgb(p.get("bg_color")) if "bg_color" in p else brand_colors.secondary
            bd = hex_to_rgb(p.get("border_color")) if "border_color" in p else brand_colors.primary
            tc = hex_to_rgb(p.get("text_color")) if "text_color" in p else (255, 255, 255)
            pills.append(PillElement(
                text=p.get("text", ""),
                pos=(p.get("x", 540), p.get("y", 700)),
                font_size=p.get("font_size", 38),
                bg_color=bg,
                border_color=bd,
                text_color=tc
            ))

        sc_type = sc.get("type", sc.get("scene_type", "standard"))

        mockup = None
        # Mockups are optional and NEVER attached to CTA search scenes!
        if sc_type != "cta" and "mockup" in sc and sc["mockup"] and isinstance(sc["mockup"], dict):
            m = sc["mockup"]
            if m.get("enabled", True):
                img_p = m.get("image", m.get("image_path", ""))
                if img_p and not os.path.isabs(img_p):
                    img_p = os.path.join(project_dir, img_p)
                # Resolve multiple images if provided
                raw_images = m.get("images", [])
                resolved_images = []
                for rip in raw_images:
                    p = os.path.join(project_dir, rip) if not os.path.isabs(rip) else rip
                    if os.path.exists(p):
                        resolved_images.append(p)

                if (img_p and os.path.exists(img_p)) or resolved_images:
                    primary_img = img_p if (img_p and os.path.exists(img_p)) else resolved_images[0]
                    mockup = MockupElement(
                        image_path=primary_img,
                        y=m.get("y", 1340),
                        width=m.get("width", 430),
                        aspect_ratio=m.get("aspect_ratio"),
                        animate=m.get("animate", "pop_in"),
                        card=m.get("card", True),
                        images=resolved_images if resolved_images else None,
                        blur_bg=m.get("blur_bg", False)
                    )

        # Parse icons
        icons = []
        for ic in sc.get("icons", []):
            ic_name = ic.get("name", ic.get("icon", ""))
            icons.append(IconElement(
                name=ic_name,
                pos=(ic.get("x", 540), ic.get("y", 1380)),
                size=ic.get("size", 160),
                animation=ic.get("animation", "pop_bounce"),
                start=float(ic["start"]) if ("start" in ic and ic["start"] is not None) else None,
                end=float(ic["end"]) if ("end" in ic and ic["end"] is not None) else None,
                label=ic.get("label"),
                label_color=hex_to_rgb(ic.get("label_color")) if "label_color" in ic else None
            ))

        # Parse code_card
        code_card = None
        if "code_card" in sc and isinstance(sc["code_card"], dict):
            cc = sc["code_card"]
            code_card = CodeCardElement(
                title=cc.get("title", "tazara_pos.py"),
                code_lines=cc.get("code_lines", cc.get("code", [])),
                pos=(cc.get("x", 540), cc.get("y", 1380)),
                width=cc.get("width", 860),
                language=cc.get("language", "python"),
                animation=cc.get("animation", "typewriter"),
                start=float(cc["start"]) if ("start" in cc and cc["start"] is not None) else None,
                end=float(cc["end"]) if ("end" in cc and cc["end"] is not None) else None
            )

        # Parse comparison
        comparison = None
        if "comparison" in sc and isinstance(sc["comparison"], dict):
            cmp = sc["comparison"]
            old_p = cmp.get("old_image", "")
            if old_p and not os.path.isabs(old_p):
                old_p = os.path.join(project_dir, old_p)
            new_p = cmp.get("new_image", "")
            if new_p and not os.path.isabs(new_p):
                new_p = os.path.join(project_dir, new_p)
            comparison = ComparisonElement(
                old_title=cmp.get("old_title", "الأنظمة القديمة ❌"),
                new_title=cmp.get("new_title", "واجهة تازارا ✅"),
                old_image=old_p if (old_p and os.path.exists(old_p)) else None,
                new_image=new_p if (new_p and os.path.exists(new_p)) else None,
                old_desc=cmp.get("old_desc", "كئيبة ومعقدة"),
                new_desc=cmp.get("new_desc", "عصرية وتفتح النفس"),
                pos=(cmp.get("x", 540), cmp.get("y", 1360)),
                width=cmp.get("width", 920),
                animation=cmp.get("animation", "pop_split")
            )

        # Parse badges
        badges = []
        for bg in sc.get("badges", []):
            badges.append(BadgeWidgetElement(
                text=bg.get("text", ""),
                status=bg.get("status", "success"),
                icon=bg.get("icon"),
                pos=(bg.get("x", 540), bg.get("y", 420)),
                animation=bg.get("animation", "slide_down"),
                start=float(bg["start"]) if ("start" in bg and bg["start"] is not None) else None,
                end=float(bg["end"]) if ("end" in bg and bg["end"] is not None) else None
            ))

        raw_scenes_parsed.append(SceneConfig(
            id=sc_id,
            start=float(sc.get("start", 0.0)),
            end=float(sc.get("end", total_dur)),
            scene_type=sc_type,
            texts=texts,
            pills=pills,
            mockup=mockup,
            icons=icons,
            code_card=code_card,
            comparison=comparison,
            badges=badges,
            custom_bg=sc.get("custom_bg"),
            transition=sc.get("transition", "none"),
            camera_drift=sc.get("camera_drift", True),
            screen_shake=sc.get("screen_shake"),
            bg_motion=sc.get("bg_motion")
        ))

    # Sort strictly by start time to prevent any timeline collisions
    raw_scenes_parsed.sort(key=lambda s: s.start)

    # Enforce strictly non-overlapping timeline: each scene ends cleanly when next begins
    for i in range(len(raw_scenes_parsed) - 1):
        if raw_scenes_parsed[i].end > raw_scenes_parsed[i + 1].start:
            raw_scenes_parsed[i].end = raw_scenes_parsed[i + 1].start

    if raw_scenes_parsed:
        raw_scenes_parsed[-1].end = max(raw_scenes_parsed[-1].end, total_dur)

    scenes_list = raw_scenes_parsed

    # Background image resolution
    bg_img = raw.get("background_image", raw.get("bg_image"))
    resolved_bg = None
    if bg_img:
        resolved_bg = os.path.join(project_dir, bg_img) if not os.path.isabs(bg_img) else bg_img
    else:
        for std_bg in ["assets/images.jpeg", "assets/background.png", "images.jpeg"]:
            bp = os.path.join(project_dir, std_bg)
            if os.path.exists(bp):
                resolved_bg = bp
                break

    reel_num = raw.get("reel_number", raw.get("video_number", b_raw.get("reel_number", "فيديو 01")))
    bg_preset = raw.get("background_preset", raw.get("bg_preset", "cyber_grid"))

    return ProjectConfig(
        project_dir=project_dir,
        title=raw.get("project_name", raw.get("title", os.path.basename(project_dir))),
        width=width,
        height=height,
        fps=fps,
        total_duration=total_dur,
        brand=brand,
        reel_number=reel_num,
        audio=audio,
        scenes=scenes_list,
        background_image=resolved_bg,
        background_preset=bg_preset
    )

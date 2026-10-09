import os
import json
from typing import Dict, List, Any

SFX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "my sfx"))
FONTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "fonts"))

BACKGROUND_PRESETS = [
    {
        "id": "cyber_grid",
        "name": "الشبكة السيبرانية (Cyber Grid)",
        "description": "خلفية تقنية داكنة مع خطوط شبكة زرقاء وهوية برمجية حديثة.",
        "best_for": ["tech", "coding", "software", "crypto"]
    },
    {
        "id": "studio_minimal",
        "name": "سبوت لايت سينمائي (Studio Minimal)",
        "description": "تدرج ناعم مع إضاءة مركزية في المنتصف يعطي تركيزاً عالياً على النصوص والمنتجات.",
        "best_for": ["business", "ecommerce", "luxury", "courses"]
    },
    {
        "id": "aurora_glow",
        "name": "أمواج الشفق (Aurora Glow)",
        "description": "أمواج ضوئية زمردية وسماوية انسيابية تمنح عمقاً حيوياً.",
        "best_for": ["modern_startup", "ai", "finance", "mobile_apps"]
    },
    {
        "id": "sunset_neon",
        "name": "تدرج الغروب النيون (Sunset Neon)",
        "description": "تدرج بنفسجي ملكي مع وميض كهرماني دافئ وجذاب للمشاهدة.",
        "best_for": ["personal_brand", "marketing", "viral_hooks"]
    },
    {
        "id": "brand_custom",
        "name": "إضاءة الهوية المخصصة (Brand Custom)",
        "description": "إضاءة ناعمة تتولد ديناميكياً من ألوان البراند الخاصة بك.",
        "best_for": ["any_brand"]
    }
]

ANIMATION_STYLES = [
    {
        "id": "typewriter",
        "name": "الآلة الكاتبة (Typewriter)",
        "description": "ظهور الحروف بالتتابع بشكل سريع واحترافي ممتاز لقراءة الهوك والمعلومات.",
        "recommended_speed": 1.8
    },
    {
        "id": "elastic_bounce",
        "name": "الارتداد المرن (Elastic Bounce)",
        "description": "ظهور سريع مع ارتداد فيزيائي جذاب جداً للأرقام والكلمات المفتاحية.",
        "recommended_speed": 1.5
    },
    {
        "id": "karaoke",
        "name": "كاريوكي الكلمات (Karaoke Highlight)",
        "description": "إضاءة كل كلمة باللون الأصفر أو الأخضر بالتزامن مع نطق الكلمة.",
        "recommended_speed": 1.0
    },
    {
        "id": "fade_up",
        "name": "الصعود الناعم (Fade Up Float)",
        "description": "صعود انسيابي من الأسفل للأعلى مع تلاشي للشفافية.",
        "recommended_speed": 1.4
    },
    {
        "id": "static",
        "name": "ثابت (Static Clean)",
        "description": "ظهور مباشر بدون حركة للنصوص العريضة.",
        "recommended_speed": 1.0
    }
]

def get_sfx_library() -> List[Dict[str, Any]]:
    """Scans and categorizes all SFX in the library."""
    items = []
    if not os.path.exists(SFX_DIR):
        return items

    category_map = {
        "hit": ("ضربة تأكيد الهوك (Punchy Hit)", "hooks"),
        "whoosh": ("انتقال سريع (Air Whoosh)", "transitions"),
        "riser": ("تصعيد سينمائي (Tension Riser)", "risers"),
        "shutter": ("التقاط كاميرا (Camera Shutter)", "ui"),
        "zoom": ("تكبير بصري (Goggles Zoom)", "transitions"),
        "pencil": ("كتابة قلم (Pencil Paper)", "writing"),
        "vision": ("انتقال رؤية (Vision FX)", "transitions"),
        "glitch": ("تأثير جليتش تقني (Sci-Fi Glitch)", "tech"),
        "money": ("عد نقود وأرباح (Money Counter)", "business"),
        "cashier": ("صوت الكاشير والشراء (Ching Cashier)", "business"),
        "clock": ("تكتكة ساعة ومهلة (Clock Ticker)", "urgency"),
        "typing": ("كتابة كيبورد حية (Keyboard Typing)", "tech"),
        "waterphone": ("غموض وترقب (Waterphone Horror)", "hooks"),
        "horn": ("صافرة إنذار وتنبيه (Angry Siren)", "hooks"),
        "scribble": ("شخبطة سريعة (Scribble)", "writing")
    }

    for fname in sorted(os.listdir(SFX_DIR)):
        if fname.endswith((".mp3", ".wav")):
            fl = fname.lower()
            cat = "general"
            label = fname
            for key, (lab, c) in category_map.items():
                if key in fl:
                    label = lab
                    cat = c
                    break
            items.append({
                "filename": fname,
                "label": label,
                "category": cat,
                "file_path": os.path.join(SFX_DIR, fname)
            })
    return items

def get_fonts_library() -> List[Dict[str, Any]]:
    """Lists all available high quality Arabic fonts."""
    fonts = []
    if os.path.exists(FONTS_DIR):
        for f in sorted(os.listdir(FONTS_DIR)):
            if f.endswith((".ttf", ".otf")):
                name = f.replace("-", " ").replace(".ttf", "").replace(".otf", "")
                fonts.append({
                    "id": f,
                    "name": name,
                    "file_path": os.path.join(FONTS_DIR, f)
                })
    return fonts

def get_complete_library_catalog() -> Dict[str, Any]:
    """Returns a unified master catalog of all engine capabilities for users & Grok AI."""
    return {
        "background_presets": BACKGROUND_PRESETS,
        "animation_styles": ANIMATION_STYLES,
        "sfx_library": get_sfx_library(),
        "fonts_library": get_fonts_library()
    }

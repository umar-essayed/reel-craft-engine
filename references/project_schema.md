# Project Schema Reference (`project.json`)

The following schema defines the complete configuration for building a video reel in Reel Craft Engine.

```json
{
  "project_name": "String: Descriptive title of the reel",
  "reel_number": "String: Optional series tag, e.g., 'فيديو 07'",
  "background_preset": "cyber_grid | dark_clean | tech_circuit",
  "total_duration": 45.0,
  "settings": {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "total_duration": 45.0
  },
  "brand": {
    "name": "Brand Name",
    "tagline": "Brand Tagline or Subtitle",
    "logo": "assets/logo.png",
    "colors": {
      "primary": "#B7EC03",
      "secondary": "#00E5FF",
      "accent": "#B7EC03",
      "background": "#000000",
      "text_primary": "#FFFFFF",
      "highlight": "#B7EC03"
    }
  },
  "audio": {
    "voiceover": "path/to/voiceover.mp3",
    "hook_boost_db": 5.0,
    "hook_duration": 3.0,
    "sfx": [
      {
        "file": "Hit.mp3",
        "time": 0.0,
        "volume": 1.0
      },
      {
        "file": "whoosh_fast.mp3",
        "time": 4.5,
        "volume": 0.8
      }
    ]
  },
  "scenes": [
    {
      "scene_id": "scene_01",
      "start_time": 0.0,
      "end_time": 4.5,
      "transition_in": "zoom_punch",
      "transition_out": "cut",
      "elements": [
        {
          "type": "icon",
          "source": "assets/icons_3d/zap.png",
          "size": 180,
          "position": {"x": 540, "y": 720},
          "animation": "pop_bounce",
          "glow": true
        },
        {
          "type": "code_card",
          "title": "keyboard_handler.rs",
          "language": "rust",
          "code": "fn handle_key(key: Key) {\n    instant_dispatch(key);\n}",
          "position": {"x": 540, "y": 740},
          "animation": "slide_up_fade"
        },
        {
          "type": "badge",
          "text": "استجابة فورية 0ms",
          "variant": "success",
          "position": {"x": 540, "y": 420}
        },
        {
          "type": "text",
          "text": "النص الكامل للمشهد باللغة العربية",
          "font_size": 52,
          "color": "#FFFFFF",
          "highlight_color": "#B7EC03",
          "position": {"x": 540, "y": 1050},
          "word_sync": [
            {"word": "النص", "start": 0.0, "end": 0.4},
            {"word": "الكامل", "start": 0.4, "end": 0.9}
          ]
        }
      ]
    }
  ]
}
```

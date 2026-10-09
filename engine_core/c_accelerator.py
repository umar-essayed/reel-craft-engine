import os
import ctypes
import numpy as np
from PIL import Image

_LIB = None
_SO_PATH = os.path.join(os.path.dirname(__file__), "accelerator.so")

if os.path.exists(_SO_PATH):
    try:
        _LIB = ctypes.CDLL(_SO_PATH)
        # void cpp_blend_rgba(uint8_t* base, const uint8_t* overlay, int width, int height, float opacity)
        _LIB.cpp_blend_rgba.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_float
        ]
        _LIB.cpp_blend_rgba.restype = None

        # void cpp_generate_background(uint8_t* buffer, int width, int height, float time)
        _LIB.cpp_generate_background.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_float
        ]
        _LIB.cpp_generate_background.restype = None
    except Exception as e:
        _LIB = None

def generate_procedural_background(width: int, height: int, t: float) -> Image.Image:
    """Generates an animated procedural shader background using C++ if available."""
    if _LIB is not None:
        buffer = np.zeros((height, width, 4), dtype=np.uint8)
        _LIB.cpp_generate_background(
            buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            width,
            height,
            ctypes.c_float(t)
        )
        return Image.fromarray(buffer, "RGBA")
    
    # Pure Python fallback
    img = Image.new("RGBA", (width, height), (8, 20, 38, 255))
    return img

def fast_blend_rgba(base_img: Image.Image, overlay_img: Image.Image, opacity: float = 1.0) -> Image.Image:
    """Blends overlay onto base using C++ SIMD routine or Pillow fallback."""
    if _LIB is not None and base_img.size == overlay_img.size:
        base_arr = np.array(base_img, dtype=np.uint8)
        overlay_arr = np.array(overlay_img, dtype=np.uint8)
        _LIB.cpp_blend_rgba(
            base_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            overlay_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
            base_img.width,
            base_img.height,
            ctypes.c_float(opacity)
        )
        return Image.fromarray(base_arr, "RGBA")
    
    return Image.alpha_composite(base_img, overlay_img)

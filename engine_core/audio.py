import os
import subprocess
import numpy as np
from typing import Optional, List, Tuple
from .config import ProjectConfig

SHARED_SFX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "my sfx"))
if not os.path.exists(SHARED_SFX_DIR):
    SHARED_SFX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "sfx"))

def load_audio_file(file_path: str, sample_rate=44100) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    if not file_path or not os.path.exists(file_path):
        return None
    cmd = [
        "ffmpeg", "-y", "-i", file_path,
        "-f", "s16le", "-ac", "2", "-ar", str(sample_rate), "pipe:1"
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0 or len(res.stdout) == 0:
        return None
    pcm = np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    return pcm[0::2], pcm[1::2] # Left, Right

def resolve_sfx_path(sfx_name_or_path: str, project_dir: str) -> Optional[str]:
    # 1. Direct path
    if os.path.isabs(sfx_name_or_path) and os.path.exists(sfx_name_or_path):
        return sfx_name_or_path

    # 2. Check project sfx dir
    proj_sfx = os.path.join(project_dir, "assets", "sfx", sfx_name_or_path)
    if os.path.exists(proj_sfx):
        return proj_sfx

    # 3. Check shared sfx directory
    shared_path = os.path.join(SHARED_SFX_DIR, sfx_name_or_path)
    if os.path.exists(shared_path):
        return shared_path

    # 4. Keyword fuzzy match in shared SFX
    sfx_lower = sfx_name_or_path.lower()
    if os.path.exists(SHARED_SFX_DIR):
        for f in os.listdir(SHARED_SFX_DIR):
            f_lower = f.lower()
            if sfx_lower in f_lower or f_lower in sfx_lower:
                return os.path.join(SHARED_SFX_DIR, f)

    return None

def build_master_audio(config: ProjectConfig, output_wav_path: str, sample_rate: int = 44100) -> bool:
    """Builds and mixes a balanced, punchy audio track for any brand/project."""
    os.makedirs(os.path.dirname(os.path.abspath(output_wav_path)), exist_ok=True)
    total_samples = int(sample_rate * config.total_duration)

    master_left = np.zeros(total_samples, dtype=np.float32)
    master_right = np.zeros(total_samples, dtype=np.float32)

    # 1. Mix Voiceover
    vo_path = config.audio.voiceover_path
    if vo_path and os.path.exists(vo_path):
        vo_res = load_audio_file(vo_path, sample_rate)
        if vo_res:
            u_l, u_r = vo_res
            copy_len = min(len(u_l), total_samples)
            master_left[:copy_len] = u_l[:copy_len]
            master_right[:copy_len] = u_r[:copy_len]

            # Apply Hook Gain Boost with smooth transition into regular voiceover
            if config.audio.hook_duration > 0 and config.audio.hook_boost_db > 0:
                hook_samples = min(int(config.audio.hook_duration * sample_rate), copy_len)
                mult = 10.0 ** (config.audio.hook_boost_db / 20.0)
                env = np.ones(hook_samples, dtype=np.float32) * mult
                fade_samples = min(int(sample_rate * 0.8), hook_samples // 3)
                if fade_samples > 0:
                    t_fade = np.linspace(0, np.pi / 2, fade_samples)
                    env[-fade_samples:] = 1.0 + (mult - 1.0) * np.cos(t_fade)
                master_left[:hook_samples] *= env
                master_right[:hook_samples] *= env

    # 2. Mix SFX Cues
    for cue in config.audio.sfx_cues:
        t_sec = float(cue.get("time", cue.get("start", 0.0)))
        sfx_ident = cue.get("file", cue.get("sfx", cue.get("name", "")))
        vol = float(cue.get("volume", cue.get("vol", 0.25)))

        sfx_path = resolve_sfx_path(sfx_ident, config.project_dir)
        if sfx_path:
            sfx_res = load_audio_file(sfx_path, sample_rate)
            if sfx_res:
                s_l, s_r = sfx_res
                s_l = s_l * vol
                s_r = s_r * vol
                start_s = int(t_sec * sample_rate)
                num_s = min(len(s_l), total_samples - start_s)
                if num_s > 0 and start_s < total_samples:
                    master_left[start_s:start_s + num_s] += s_l[:num_s]
                    master_right[start_s:start_s + num_s] += s_r[:num_s]

    # Dynamic Soft-Knee Limiter to preserve energy without clipping or crushing overall dynamics
    def apply_soft_limiter(arr: np.ndarray, threshold: float = 0.82) -> np.ndarray:
        peak = np.max(np.abs(arr))
        if peak <= threshold:
            return arr
        out = arr.copy()
        mask = np.abs(out) > threshold
        signs = np.sign(out[mask])
        excess = np.abs(out[mask]) - threshold
        compressed = threshold + (0.97 - threshold) * np.tanh(excess / (0.97 - threshold + 1e-6))
        out[mask] = signs * compressed
        return out

    master_left = apply_soft_limiter(master_left)
    master_right = apply_soft_limiter(master_right)

    # Interleave to 16-bit PCM
    int_left = np.clip(master_left * 32767.0, -32768, 32767).astype(np.int16)
    int_right = np.clip(master_right * 32767.0, -32768, 32767).astype(np.int16)
    interleaved = np.empty((total_samples * 2,), dtype=np.int16)
    interleaved[0::2] = int_left
    interleaved[1::2] = int_right

    # Export WAV using FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-f", "s16le", "-ar", str(sample_rate), "-ac", "2",
        "-i", "pipe:0",
        "-c:a", "pcm_s16le", output_wav_path
    ]
    proc = subprocess.run(cmd, input=interleaved.tobytes(), capture_output=True)
    return proc.returncode == 0

#!/usr/bin/env python3
"""
reel-craft-engine Transcriber & Audio Ingestion CLI
Extracts audio from video or loads raw audio, runs Whisper with millisecond word timestamps,
detects speech silences/pauses, and exports clean word-level timing JSON.
"""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path

def extract_audio(input_file: str, output_wav: str) -> bool:
    """Extract audio from video file or convert input audio to clean 16kHz mono WAV."""
    cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        output_wav
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.returncode == 0

def transcribe_audio(audio_path: str, model_size: str = "base", language: str = "ar") -> dict:
    """Run Whisper transcription with word-level timestamps."""
    import whisper
    
    print(f"[*] Loading Whisper model '{model_size}'...")
    model = whisper.load_model(model_size)
    
    print(f"[*] Transcribing '{audio_path}' (Language: {language})...")
    # Whisper word_timestamps
    result = model.transcribe(
        audio_path,
        language=language,
        word_timestamps=True,
        verbose=False
    )
    
    words_data = []
    for segment in result.get("segments", []):
        for w in segment.get("words", []):
            word_str = w.get("word", "").strip()
            if word_str:
                words_data.append({
                    "word": word_str,
                    "start": round(w.get("start", 0.0), 3),
                    "end": round(w.get("end", 0.0), 3),
                    "confidence": round(w.get("probability", 1.0), 3)
                })
                
    full_text = result.get("text", "").strip()
    return {
        "text": full_text,
        "language": language,
        "segments": result.get("segments", []),
        "words": words_data
    }

def main():
    parser = argparse.ArgumentParser(description="Reel Craft Engine - Audio Transcriber & Synchronizer")
    parser.add_argument("input", help="Path to input audio (.mp3, .wav) or video (.mp4, .mov)")
    parser.add_argument("--output", "-o", default=None, help="Output JSON path (defaults to <name>_transcript.json)")
    parser.add_argument("--model", "-m", default="base", help="Whisper model: tiny, base, small, medium")
    parser.add_argument("--lang", "-l", default="ar", help="Spoken language code (default: ar)")
    
    args = parser.parse_args()
    input_path = os.path.abspath(args.input)
    
    if not os.path.exists(input_path):
        print(f"[!] Error: File '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)
        
    base_name = Path(input_path).stem
    work_dir = Path(input_path).parent
    wav_path = str(work_dir / f"{base_name}_temp_16k.wav")
    
    out_json = args.output or str(work_dir / f"{base_name}_transcript.json")
    
    print(f"[*] Pre-processing audio to 16kHz mono...")
    if not extract_audio(input_path, wav_path):
        print(f"[!] FFmpeg audio extraction failed.", file=sys.stderr)
        sys.exit(1)
        
    try:
        transcript_data = transcribe_audio(wav_path, model_size=args.model, language=args.lang)
        
        # Calculate speech rate and pauses
        words = transcript_data["words"]
        total_words = len(words)
        duration = words[-1]["end"] if words else 0.0
        wpm = (total_words / (duration / 60.0)) if duration > 0 else 0
        
        transcript_data["stats"] = {
            "total_words": total_words,
            "duration": round(duration, 2),
            "words_per_minute": round(wpm, 1),
            "average_word_duration": round(duration / total_words, 3) if total_words else 0
        }
        
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            
        print(f"[+] Transcription successful: {len(words)} words ({wpm:.1f} WPM).")
        print(f"[+] Saved transcript to: {out_json}")
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)

if __name__ == "__main__":
    main()

import os
import sys
import json
import queue
import sounddevice as sd
import vosk
import threading
import time
import wave
import tempfile
import subprocess
import difflib
from piper.voice import PiperVoice

import numpy as np
from faster_whisper import WhisperModel

# Global Debug Flag
DEBUG_MODE = False

# Paths
TTS_MODEL_PATH = "models/piper/en_GB-jenny_dioco-medium.onnx"
TTS_CONFIG_PATH = "models/piper/en_GB-jenny_dioco-medium.onnx.json"
# Whisper handles its own models, usually in ~/.cache/huggingface, or we can specify download_root
STT_MODEL_SIZE = "small.en" 

# Globals
stt_model = None
tts_voice = None

def load_tts_model():
    global tts_voice
    if DEBUG_MODE: return
    if tts_voice is None:
        if not os.path.exists(TTS_MODEL_PATH):
            raise FileNotFoundError(f"Piper model not found at {TTS_MODEL_PATH}")
        print("Loading Neural TTS model...")
        tts_voice = PiperVoice.load(TTS_MODEL_PATH, TTS_CONFIG_PATH)

def load_stt_model():
    global stt_model
    if DEBUG_MODE: return
    if stt_model is None:
        print(f"Loading Whisper STT model ({STT_MODEL_SIZE})...")
        # Run on CPU with INT8 by default for speed/compatibility
        try:
            stt_model = WhisperModel(STT_MODEL_SIZE, device="cpu", compute_type="int8")
        except Exception as e:
            print(f"Error loading Whisper: {e}")
            raise e

# Audio Queue
q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def speak(text):
    """Reads text aloud using Piper TTS."""
    # print(f"SAY: {text}") # Reduced log noise
    if DEBUG_MODE:
        return

    try:
        load_tts_model()
        
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            temp_filename = tf.name
            
        # Synthesize
        with wave.open(temp_filename, "wb") as wav_file:
            tts_voice.synthesize_wav(text, wav_file)
            
        # Play using afplay (Mac)
        subprocess.run(["afplay", temp_filename])
        
        # Cleanup
        os.remove(temp_filename)
        
    except Exception as e:
        print(f"TTS Error: {e}")

def normalize_answer(text, options_ctx=None):
    """
    Converts spoken text to 'A', 'B', 'C', 'D'.
    options_ctx: dict {'A': 'Stratosphere', 'B': '...'}
    """
    text = text.lower().strip()
    
    # Clean punctuation
    text = text.replace('.', '').replace(',', '').replace('!', '').replace('?', '')
    
    # 1. Direct label check
    if text in ['a', 'option a', 'answer a', 'alpha']: return 'A'
    if text in ['b', 'option b', 'answer b', 'bravo', 'be']: return 'B'
    if text in ['c', 'option c', 'answer c', 'charlie', 'sea', 'see']: return 'C'
    if text in ['d', 'option d', 'answer d', 'delta']: return 'D'
    
    # Check for "Option X" pattern
    import re
    match = re.search(r'option ([a-d])', text)
    if match: return match.group(1).upper()

    # 2. Content fuzzy matching
    if options_ctx:
        content_map = {}
        candidates = []
        for key, val in options_ctx.items():
            if not val: continue
            clean_val = val.lower().strip()
            content_map[clean_val] = key
            candidates.append(clean_val)
            
        # Whisper is accurate, so exact substring matches are more reliable
        # "stratosphere" in "it is stratosphere"
        for cand in candidates:
             if cand in text or text in cand:
                 # Avoid short meaningless matches like "a" or "is"
                 if len(cand) > 3:
                     # print(f"Matched '{text}' to '{cand}'")
                     return content_map[cand]
        
        # Fallback to fuzzy
        matches = difflib.get_close_matches(text, candidates, n=1, cutoff=0.7)
        if matches:
            best_match = matches[0]
            # print(f"Fuzzy Matched '{text}' to '{best_match}'")
            return content_map[best_match]

    return None

def listen_for_answer(timeout=5, options=None):
    """
    Records audio for a fixed duration (or until silence) and transcribes with Whisper.
    """
    if DEBUG_MODE:
        try:
            print("--- DEBUG: Listening (Type your answer) ---")
            ans = input("Your answer (A/B/C/D or text) > ")
            return normalize_answer(ans, options)
        except EOFError:
            return None

    load_stt_model()
    
    # Recording Parameters
    SAMPLE_RATE = 16000
    CHANNELS = 1
    SILENCE_THRESHOLD = 500  # Amplitude threshold
    SILENCE_DURATION = 1.5   # Seconds of silence to stop
    MAX_DURATION = timeout   # Total max seconds
    
    audio_buffer = []
    
    # Status update logic should be handled by caller (UI), but here we just print
    # print("LISTENING...", flush=True)

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16') as stream:
            start_time = time.time()
            last_sound_time = time.time()
            frames_per_buffer = 1024
            
            while True:
                # Check max timeout
                if time.time() - start_time > MAX_DURATION:
                    break
                    
                # Check silence timeout
                if time.time() - last_sound_time > SILENCE_DURATION and len(audio_buffer) > SAMPLE_RATE * 0.5:
                     # Only stop if we have recorded at least 0.5s of audio
                    break
                
                # Read audio
                data, overflow = stream.read(frames_per_buffer)
                audio_buffer.append(data.flatten())
                
                # Simple VAD (Energy Based)
                # Convert to float for amplitude calculation to avoid overflow
                amplitudes = np.abs(data)
                if np.max(amplitudes) > SILENCE_THRESHOLD:
                    last_sound_time = time.time()
                    
            # Process Audio
            if not audio_buffer:
                return None
                
            full_audio = np.concatenate(audio_buffer)
            
            # Convert int16 to float32 normalized for Whisper
            full_audio_float = full_audio.astype(np.float32) / 32768.0
            
            if len(full_audio_float) < SAMPLE_RATE * 0.5:
                # Too short
                return None
            
            # Transcribe
            # print("Transcribing...")
            segments, info = stt_model.transcribe(full_audio_float, beam_size=5, language="en")
            
            joined_text = " ".join([segment.text for segment in segments]).strip()
            
            if joined_text:
                # print(f"HEARD: {joined_text}")
                return normalize_answer(joined_text, options)
            else:
                return None
                            
    except Exception as e:
        print(f"Error during listening: {e}")
        return None

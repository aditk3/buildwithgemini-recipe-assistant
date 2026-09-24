import math
import numpy as np
from scipy.io import wavfile

def generate_lofi_track(filename="lofi_music.wav", duration_sec=30, sample_rate=44100):
    num_samples = sample_rate * duration_sec
    time = np.linspace(0, duration_sec, num_samples, endpoint=False)
    
    # 85 BPM beat timing
    bpm = 85
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4
    
    # Chord frequencies (Hz)
    chords = [
        # Fmaj7: F3, A3, C4, E4
        [174.61, 220.00, 261.63, 329.63],
        # Em7: E3, G3, B3, D4
        [164.81, 196.00, 246.94, 293.66],
        # Dm7: D3, F3, A3, C4
        [146.83, 174.61, 220.00, 261.63],
        # Cmaj7: C3, E3, G3, B3
        [130.81, 164.81, 196.00, 246.94]
    ]
    
    audio = np.zeros(num_samples)
    
    # Generate warm synth chords
    for t_idx in range(num_samples):
        t = time[t_idx]
        bar_idx = int(t / bar_sec) % len(chords)
        chord_freqs = chords[bar_idx]
        
        # Envelope for gentle strumming/fade
        bar_t = t % bar_sec
        env = np.exp(-1.2 * (bar_t % (bar_sec / 2))) * 0.4 + 0.3
        
        chord_val = 0.0
        for f in chord_freqs:
            # Soft sine + subtle 2nd harmonic
            chord_val += np.sin(2 * np.pi * f * t) * 0.25 + np.sin(2 * np.pi * f * 2 * t) * 0.05
        
        audio[t_idx] += chord_val * env
    
    # Add bassline
    bass_freqs = [174.61 / 2, 164.81 / 2, 146.83 / 2, 130.81 / 2]
    for t_idx in range(num_samples):
        t = time[t_idx]
        bar_idx = int(t / bar_sec) % len(bass_freqs)
        f_bass = bass_freqs[bar_idx]
        
        beat_t = t % beat_sec
        bass_env = np.exp(-3.0 * beat_t)
        audio[t_idx] += np.sin(2 * np.pi * f_bass * t) * 0.35 * bass_env
        
    # Add upbeat drums (Kick on 1 & 3, Snare on 2 & 4, Hi-hats on 8th notes)
    for t_idx in range(num_samples):
        t = time[t_idx]
        beat_pos = (t % bar_sec) / beat_sec
        
        # Kick (beats 0 and 2)
        if (beat_pos % 2) < 0.15:
            kick_t = (beat_pos % 2) * beat_sec
            kick_freq = 120 * np.exp(-25 * kick_t) + 40
            audio[t_idx] += np.sin(2 * np.pi * kick_freq * kick_t) * np.exp(-10 * kick_t) * 0.5
            
        # Snare (beats 1 and 3)
        if 1.0 <= beat_pos < 1.15 or 3.0 <= beat_pos < 3.15:
            snare_t = (beat_pos % 1.0) * beat_sec
            noise = np.random.uniform(-1, 1)
            audio[t_idx] += noise * np.exp(-18 * snare_t) * 0.25
            
        # Hi-hat (every 0.5 beat)
        if (beat_pos % 0.5) < 0.08:
            hat_t = (beat_pos % 0.5) * beat_sec
            noise = np.random.uniform(-1, 1)
            audio[t_idx] += noise * np.exp(-40 * hat_t) * 0.08

    # Subtle vinyl noise background
    vinyl = np.random.normal(0, 0.012, num_samples)
    audio += vinyl
    
    # Normalize audio
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val * 0.75
        
    # Convert to 16-bit PCM WAV
    audio_int16 = (audio * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, audio_int16)
    print(f"Generated upbeat lo-fi track: {filename}")

if __name__ == "__main__":
    generate_lofi_track()

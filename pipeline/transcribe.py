"""Whisper transcription with word timestamps (used to build the cut list).

Usage: python3 transcribe.py <audio_16k_mono.f32> <model> <out.json>
Input is raw float32 PCM at 16 kHz (decoded by ffmpeg) to sidestep PyAV version issues.
"""
import json, sys
import numpy as np
from faster_whisper import WhisperModel

PROMPT = ("Rawatan psikiatri. Depot injection, suntikan antipsikotik jangka panjang, skizofrenia, "
          "ubat, relapse, pesakit, Dr Azren.")


def main(pcm, model, out):
    m = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=4)
    audio = np.fromfile(pcm, dtype=np.float32)
    segs, _ = m.transcribe(audio, language="ms", word_timestamps=True, vad_filter=True, beam_size=5, initial_prompt=PROMPT)
    res = []
    for s in segs:
        res.append({"start": s.start, "end": s.end, "text": s.text,
                    "words": [{"w": w.word, "s": w.start, "e": w.end, "p": w.probability} for w in s.words]})
        print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}", flush=True)
    json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:4])

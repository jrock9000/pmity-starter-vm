#!/usr/bin/env python3
"""encode.py: turns the recorded PMITY Starter narration into the files the course page plays, and checks each one.

Input folder (from starter-voice-wav.tar): manifest.json [{label, key, text, spoken, parts}] and out/<key>-<n>.wav, the
pieces PMITY Voice recorded (husayn-default, 48 kHz mono WAV, at most 280 characters each).
For every text it joins the pieces with a short pause, writes mono MP3 at 48 kHz, 128 kbit/s (no loudness filter) to
<out>/<key>.mp3, then transcribes the joined audio (faster-whisper base.en) and scores it against the spoken text,
letters only, because a voice model can garble or drop words while its own QA passes them.

    python3 voice/encode.py <input dir> <output dir>
Writes <out>/manifest.json (what the course page reads; cli-notes R9) and <out>/report.json; exit 0 always, the report
lists texts scoring under PASS, which are re-recorded.
"""
import difflib, json, os, re, subprocess, sys, tempfile, wave

PASS = 0.90
GAP_SECONDS = 0.35


def letters(text):
    from num2words import num2words
    text = re.sub(r"(?<=\d),(?=\d{3})", "", text)
    text = re.sub(r"\d+", lambda m: " " + num2words(int(m.group(0))) + " ", text)
    return re.sub(r"[^a-z]", "", text.lower())


def join(parts, dest):
    with wave.open(parts[0]) as first:
        params = first.getparams()
    gap = b"\0" * (params.sampwidth * params.nchannels * int(params.framerate * GAP_SECONDS))
    with wave.open(dest, "wb") as out:
        out.setparams(params)
        for i, path in enumerate(parts):
            with wave.open(path) as w:
                out.writeframes((gap if i else b"") + w.readframes(w.getnframes()))
    with wave.open(dest) as w:
        return round(w.getnframes() * 1000 / w.getframerate())


def main(src, dst):
    from faster_whisper import WhisperModel
    import numpy as np
    os.makedirs(dst, exist_ok=True)
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    manifest, report = [], []
    for entry in json.load(open(os.path.join(src, "manifest.json"))):
        parts = [os.path.join(src, "out", f"{entry['key']}-{i}.wav") for i in range(entry["parts"])]
        missing = [p for p in parts if not os.path.exists(p)]
        if missing:
            report.append({"label": entry["label"], "key": entry["key"], "score": 0, "why": f"{len(missing)} piece(s) not recorded"})
            continue
        with tempfile.TemporaryDirectory() as tmp:
            joined = os.path.join(tmp, "joined.wav")
            ms = join(parts, joined)
            mp3 = os.path.join(dst, entry["key"] + ".mp3")
            # PMITY Voice already levels its output (peaks at -1.5 dBFS), so no loudness filter: a second limiter plus
            # 24 kHz / 48 kbit/s gave 17 dB signal-to-distortion, heard as hoarse static (owner, 2026-11-16).
            # 48 kHz / 128 kbit/s CBR keeps the voice service's sample rate and measures 40 dB on step 1.
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", joined,
                            "-ac", "1", "-ar", "48000", "-c:a", "libmp3lame", "-b:a", "128k", mp3], check=True)
            with wave.open(joined) as w:
                audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
                rate = w.getframerate()
            audio = audio[: len(audio) // (rate // 16000) * (rate // 16000)].reshape(-1, rate // 16000).mean(1)
            segments, _ = model.transcribe(audio, language="en", beam_size=5)
            heard = " ".join(s.text.strip() for s in segments)
        score = difflib.SequenceMatcher(None, letters(entry["spoken"]), letters(heard)).ratio()
        manifest.append({"key": entry["key"], "label": entry["label"], "text": entry["text"], "file": entry["key"] + ".mp3", "ms": ms})
        report.append({"label": entry["label"], "key": entry["key"], "score": round(score, 3), "ms": ms,
                       "bytes": os.path.getsize(mp3), "spoken": entry["spoken"], "heard": heard})
        print(f"{entry['label']:8} {score:.3f} {ms / 1000:6.1f}s", flush=True)
    json.dump(manifest, open(os.path.join(dst, "manifest.json"), "w"), indent=1)
    json.dump(report, open(os.path.join(dst, "report.json"), "w"), indent=1)
    low = [r for r in report if r["score"] < PASS]
    print(f"{len(manifest)} files, {sum(r.get('bytes', 0) for r in report) / 1e6:.1f} MB, "
          f"{sum(r.get('ms', 0) for r in report) / 60000:.1f} min; under {PASS}: {', '.join(r['label'] for r in low) or 'none'}")


if __name__ == "__main__":
    main(*sys.argv[1:3])

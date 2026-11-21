"""Generate lesson narration MP3s via the ElevenLabs API.
Runs inside GitHub Actions; the API key comes from the repo secret
ELEVENLABS_API_KEY and never appears in the repository or the page.
"""
import json, os, sys, time, urllib.request

KEY = os.environ["ELEVENLABS_API_KEY"]
VOICE = os.environ.get("VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel
MODEL = os.environ.get("MODEL_ID", "eleven_multilingual_v2")

lessons = json.load(open("scripts/lessons.json"))
os.makedirs("audio", exist_ok=True)

for l in lessons:
    out = f"audio/lesson-{l['n']:02d}.mp3"
    if os.path.exists(out) and os.path.getsize(out) > 1000 and os.environ.get("FORCE") != "1":
        print(f"skip {out} (exists)")
        continue
    body = json.dumps({"text": l["text"], "model_id": MODEL}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128",
        data=body,
        headers={"xi-api-key": KEY, "Content-Type": "application/json"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                audio = r.read()
            open(out, "wb").write(audio)
            print(f"wrote {out} ({len(audio)//1024} KB) - {l['title']}")
            break
        except Exception as e:
            print(f"attempt {attempt+1} failed for {out}: {e}")
            if attempt == 2:
                sys.exit(1)
            time.sleep(5)
print("done")

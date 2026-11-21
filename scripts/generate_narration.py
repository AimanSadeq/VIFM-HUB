"""Generate lesson narration MP3s via the ElevenLabs API.
Runs inside GitHub Actions; the API key comes from the repo secret
ELEVENLABS_API_KEY and never appears in the repository or the page.
"""
import json, os, sys, time, urllib.request, urllib.error

KEY = os.environ["ELEVENLABS_API_KEY"].strip()
VOICE = (os.environ.get("VOICE_ID") or "21m00Tcm4TlvDq8ikWAM").strip()
MODEL = (os.environ.get("MODEL_ID") or "eleven_multilingual_v2").strip()
NAME = (os.environ.get("VOICE_NAME") or "").strip()

def api(path, data=None):
    req = urllib.request.Request(
        "https://api.elevenlabs.io" + path, data=data,
        headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

if NAME:
    voices = json.loads(api("/v1/voices")).get("voices", [])
    match = next((v for v in voices if v["name"].lower() == NAME.lower()), None)
    if not match:
        print(f"Voice named '{NAME}' not found. Available:")
        for v in voices: print(" -", v["name"], v["voice_id"])
        sys.exit(1)
    VOICE = match["voice_id"]
    print(f"Using voice: {match['name']} ({VOICE})")

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
        except urllib.error.HTTPError as e:
            print(f"attempt {attempt+1} failed for {out}: {e} :: {e.read().decode(errors='replace')[:500]}")
            if attempt == 2:
                sys.exit(1)
            time.sleep(5)
        except Exception as e:
            print(f"attempt {attempt+1} failed for {out}: {e}")
            if attempt == 2:
                sys.exit(1)
            time.sleep(5)
print("done")

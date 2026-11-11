"""Small repeatable Tamil agriculture benchmark against the LOCAL backend (127.0.0.1:8000).

Measures objective things only: instant refusals (fallback), answers cut off mid-sentence,
length, Latin-letter leakage, latency. It does NOT judge factual quality: read the answers
(JSON output) yourself. Usage: python3 scripts/tamil_bench.py out.json
"""
import json, re, sys, time, urllib.request

Q = ["நெல் இலைகள் மஞ்சளாக மாறுவது ஏன்?", "NPK உரம் என்றால் என்ன?", "மண் வளத்தை எப்படி மேம்படுத்தலாம்?",
     "பயிர் சுழற்சியின் முக்கியத்துவம் என்ன?", "வாழை நடவுக்கு நிலத்தை எப்படி தயார் செய்வது?",
     "இந்த வாரம் மழை பெய்யுமா?", "நெல் நாற்றங்காலை எப்படி தயாரிப்பது?", "மண் பரிசோதனை ஏன் செய்ய வேண்டும்?"]
out = []
for q in Q:
    t = time.time()
    req = urllib.request.Request("http://127.0.0.1:8000/conversation",
                                 data=json.dumps({"question": q, "language": "Tamil"}).encode(),
                                 headers={"Content-Type": "application/json"})
    ev, cur, buf = {}, None, []
    with urllib.request.urlopen(req, timeout=300) as r:
        for raw in r:
            l = raw.decode().rstrip("\n")
            if l.startswith("event:"): cur = l[6:].strip()
            elif l.startswith("data:"): buf.append(l[5:].strip())
            elif l == "" and buf:
                try: ev[cur] = json.loads("".join(buf))["data"]
                except Exception: pass
                buf, cur = [], None
    c = ev["completed"]; a = c["answer"]
    tam = sum(1 for ch in a if "஀" <= ch <= "௿"); lat = sum(1 for ch in a if ch.isascii() and ch.isalpha())
    o = {"q": q, "seconds": round(time.time() - t, 1), "fallback": c["is_fallback"], "mode": c.get("grounding_mode"),
         "words": len(a.split()), "ends_complete": bool(re.search(r"[.!?।]\s*$", a.strip())),
         "latin_letter_ratio": round(lat / max(1, lat + tam), 2), "answer": a}
    out.append(o)
    print(f"{o['seconds']:>5}s fb={o['fallback']!s:<5} words={o['words']:<4} complete={o['ends_complete']!s:<5} latin={o['latin_letter_ratio']} | {q}")
json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
n = len(out)
print("SUMMARY fallbacks", sum(o["fallback"] for o in out), "/", n, "| truncated endings",
      sum(not o["ends_complete"] and not o["fallback"] for o in out), "| avg words", round(sum(o["words"] for o in out) / n),
      "| avg s", round(sum(o["seconds"] for o in out) / n, 1))

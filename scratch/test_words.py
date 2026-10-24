import json
from pathlib import Path

p = Path("output/jobs/job_1792842075_e285e7/chapters/ch01/voice.words.json")
if p.exists():
    data = json.loads(p.read_text(encoding="utf-8"))["words"]
    for i in range(min(20, len(data))):
        w = data[i]
        gap = (w["start"] - data[i-1]["end"]) if i > 0 else 0
        print(f"{w['text']:16} [{w['start']:6.3f} -> {w['end']:6.3f}] dur={(w['end']-w['start'])*100:5.1f}cs  gap={gap:6.3f}s")

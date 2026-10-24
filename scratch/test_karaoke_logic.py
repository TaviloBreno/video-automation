import json
from pathlib import Path

def _fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

p = Path("output/jobs/job_1792842075_e285e7/chapters/ch01/voice.words.json")
data = json.loads(p.read_text(encoding="utf-8"))["words"]

# Agrupamento inteligente
lines = []
current = []

for i, w in enumerate(data):
    current.append(w)
    txt = w["text"].strip()
    
    # Próxima palavra para checar gap
    next_w = data[i + 1] if i + 1 < len(data) else None
    next_gap = (next_w["start"] - w["end"]) if next_w else 0.0
    
    is_strong_punct = any(txt.endswith(p) for p in [".", "!", "?", ":", "..."])
    is_comma_punct = txt.endswith(",") and len(current) >= 3
    is_pause = next_gap >= 0.32
    is_max_words = len(current) >= 5

    if is_strong_punct or is_pause or is_comma_punct or is_max_words or next_w is None:
        lines.append(current)
        current = []

if current:
    lines.append(current)

print(f"Total de linhas geradas: {len(lines)}")
for idx, group in enumerate(lines[:8]):
    start = group[0]["start"]
    end = group[-1]["end"] + 0.12  # breve respiro final
    
    karaoke_parts = []
    for j, w in enumerate(group):
        dur_cs = max(1, int(round((w["end"] - w["start"]) * 100)))
        if j > 0:
            gap = w["start"] - group[j - 1]["end"]
            if gap > 0.005:
                gap_cs = max(1, int(round(gap * 100)))
                karaoke_parts.append(f"{{\\k{gap_cs}}} ")
            else:
                karaoke_parts.append(" ")
        karaoke_parts.append(f"{{\\kf{dur_cs}}}{w['text']}")
    
    line_text = "".join(karaoke_parts)
    print(f"[{_fmt_time(start)} -> {_fmt_time(end)}] {line_text}")

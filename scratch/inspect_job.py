import re
from pathlib import Path

job_dir = Path("output/jobs/job_1793431614_085f73/chapters")
for ch_dir in sorted(job_dir.iterdir()):
    if ch_dir.is_dir():
        print(f"=== {ch_dir.name} ===")
        for h in sorted(ch_dir.glob("scene_*.html")):
            txt = h.read_text(encoding="utf-8")
            b = re.findall(r'class="hud-sub-badge"[^>]*>([^<]+)<', txt)
            l = re.findall(r'class="hud-label"[^>]*>([^<]+)<', txt)
            t = re.findall(r'class="bio-telemetry-badge"[^>]*>([^<]+)<', txt)
            print(f"  {h.name} -> badge: {b} | label: {l} | bio: {t}")


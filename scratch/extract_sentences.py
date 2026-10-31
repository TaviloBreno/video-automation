import json
from pathlib import Path

# Load all 16 sentences from job_1793431614_085f73 (Tecido Conjuntivo)
manifest_path = Path("output/jobs/job_1793431614_085f73/manifest.json")
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print("Manifest Topic:", manifest.get("topic"))
    sentences = []
    for ch in manifest.get("chapters", []):
        for sc in ch.get("scenes", []):
            sentences.append((ch.get("title", ""), sc.get("text", "")))
    print(f"Total sentences extracted: {len(sentences)}")
    for i, (title, s) in enumerate(sentences):
        print(f"[{i+1}] ({title}) {s[:70]}...")
else:
    print("Manifest not found")


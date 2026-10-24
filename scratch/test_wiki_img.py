import requests

headers = {"User-Agent": "VideoAutomation/1.0 (scientific video project; contact: tavilobreno)"}
terms = ["Cancer_cell", "Immunotherapy", "Quasar", "Black_hole", "DNA"]

for term in terms:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{term}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            img = data.get("originalimage") or data.get("thumbnail")
            desc = data.get("description", "")
            img_url = img.get("source") if img else None
            print(f"[{term}] {desc}\n  -> {img_url}\n")
    except Exception as e:
        print(f"[{term}] Erro: {e}")

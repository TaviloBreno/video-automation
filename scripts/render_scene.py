import json
import subprocess
from pathlib import Path

def render_scene_video(scene_path: str, palettes_path: str, output_path: str):
    """Renderiza o vídeo usando o HyperFrames com as variáveis da cena."""
    scene = json.loads(Path(scene_path).read_text(encoding="utf-8"))
    palettes = json.loads(Path(palettes_path).read_text(encoding="utf-8"))
    
    palette_name = scene["palette"]
    palette = palettes[palette_name]

    # Monta o objeto de variáveis para o HyperFrames
    variables = {
        "narrationText": scene["narration_text"],
        "palettePrimary": palette["primary"],
        "paletteAccent": palette["accent"],
        "paletteText": palette["text"],
        "paletteBackground": palette["background"]
    }
    
    # Comando para renderizar (substitua 'preview' por 'render' quando for gerar o MP4 final)
    # Para testar no preview, o ideal é passar as variáveis pela URL ou usar o Studio,
    # mas para automação, o comando de render é o que importa.
    # Aqui usamos o comando de render para provar que as variáveis funcionam.
    cmd = [
        "npx", "hyperframes", "render",
        "--variables", json.dumps(variables),
        "--output", output_path
    ]
    
    print(f"Executando: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    # Exemplo de uso: renderiza a cena de output/scene.json
    render_scene_video(
        scene_path="output/scene.json",
        palettes_path="config/palettes.json",
        output_path="output/final_video.mp4"
    )
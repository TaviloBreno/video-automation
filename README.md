# Video Automation

Pipeline local para transformar uma descrição em português em uma cena narrada,
renderizada, legendada e exportada para YouTube e formatos verticais.

## Requisitos

- Python 3.11 ou superior.
- FFmpeg com `ffmpeg` e `ffprobe` no `PATH`.
- Node.js LTS e npm, usados pelo render HyperFrames.
- Ollama instalado, em execução e com o modelo `llama3.2` baixado.
- `subreel` instalado e acesso à internet para a voz Edge TTS.
- Acesso à internet para pesquisa e inclusão de fontes nos vídeos (Bing).

## Instalação

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg nodejs npm
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install subreel
ollama serve
```

Em algumas distribuições, o Node.js dos repositórios é antigo. Se o render
HyperFrames falhar, instale uma versão LTS atual do Node.js pelo repositório
oficial e confirme `node --version` e `npm --version`.

### macOS

```bash
brew install python ffmpeg node
brew install ollama
ollama pull llama3.2

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install subreel
ollama serve
```

### Windows (PowerShell)

Instale Python 3.11+, FFmpeg, Node.js LTS e Ollama. Com `winget`:

```powershell
winget install --id Python.Python.3.13 --exact
winget install --id Gyan.FFmpeg --exact
winget install --id OpenJS.NodeJS.LTS --exact
winget install --id Ollama.Ollama --exact
```

Feche e reabra o PowerShell após a instalação para atualizar o `PATH`. Depois:

```powershell
ollama pull llama3.2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install subreel
```

Se a política do PowerShell impedir a ativação do ambiente virtual, use
`.\.venv\Scripts\python.exe` em vez de ativá-lo. FFmpeg deve disponibilizar
`ffmpeg.exe` e `ffprobe.exe` no `PATH`.

## Interface Web (Studio AI)

Para usar a tela interativa com criação de roteiro por tema, controle de duração em minutos e gerador de cortes virais para Shorts/Reels/TikTok:

```powershell
python run_studio.py
```
ou dê um duplo clique em `start_studio.bat`. A tela abre automaticamente no seu navegador em `http://localhost:5000`.

## Configuração e uso via CLI

Inicie o Ollama em outro terminal (`ollama serve`, caso ele não inicie como
serviço) e verifique as dependências:

```bash
python scripts/cli.py check
```

O relatório de `check` usa `[OK]`/`[ERRO]` para ser legível também em
terminais Windows com codificação CP1252.

Gere os dois formatos a partir da descrição padrão:

```bash
python scripts/cli.py all --input input/descricao.txt
```

Ou indique as opções explicitamente:

```bash
python scripts/cli.py all \
  --input input/descricao.txt \
  --palette dark-neon \
  --voice pt-BR-FranciscaNeural \
  --legend-style karaoke \
  --formats youtube,vertical
```

Por padrão, `all` e `parse` pesquisam fontes na web, entregam os resultados
como evidências ao modelo e gravam a bibliografia em `output/research.json` e
`output/scene.json`. Afirmações factuais nos elementos de texto recebem IDs de
fonte e a composição mostra as referências junto ao conteúdo. A busca usa
resultados públicos do Bing; confira as páginas originais antes de publicar.
Sem conexão ou sem fontes utilizáveis, a etapa falha com uma mensagem clara;
para executar deliberadamente sem pesquisa, use `--no-research`. O visual é
uma identidade editorial própria de explicação científica, sem reproduzir a
marca ou a identidade visual de outros canais.

No PowerShell, os comandos podem ser escritos em uma linha ou usar o acento
grave como continuação. Os arquivos finais são `output-youtube.mp4` e
`output-vertical.mp4`. Use `python scripts/cli.py --help` para ver todos os
subcomandos (`check`, `parse`, `voice`, `render`, `subs`, `export` e `all`).
Preferências persistentes podem ser editadas com, por exemplo,
`python scripts/settings.py --palette warm-sunset --voice pt-BR-FranciscaNeural`
ou pelo menu `python scripts/settings.py --interactive`.

## Testes

```bash
python -m pip install pytest pytest-cov
python -m pytest -q
python -m pytest -q --cov=scripts.scene_validator --cov=scripts.words_validator --cov=scripts.compute_duration --cov-report=term-missing
```

O teste end-to-end é marcado `slow` e executa a integração real com Ollama,
TTS, renderizador e FFmpeg. Para executá-lo isoladamente:

```bash
python -m pytest -q -m slow tests/test_pipeline_e2e.py
```

Se uma dependência externa necessária não estiver instalada ou o Ollama/modelo
não estiver disponível, o teste é pulado com o motivo exibido no relatório.

## Troubleshooting

### FFmpeg não encontrado

Confirme `ffmpeg -version` e `ffprobe -version` em um terminal novo. Instale o
FFmpeg pelo gerenciador indicado acima e adicione a pasta `bin` ao `PATH`.
No Windows, por exemplo, confira se a pasta que contém `ffmpeg.exe` e
`ffprobe.exe` está nas variáveis de ambiente do usuário/sistema.

### Ollama não responde

Execute `ollama serve` em um terminal e confira `ollama list`. Baixe o modelo
configurado com `ollama pull llama3.2`. O serviço padrão responde em
`http://localhost:11434`; se usar outra URL/modelo, ajuste `llm.base_url` e
`llm.model` em `config/config.yaml`.

### `subreel` falha

Confirme a instalação com `subreel --help`, reinstale com
`python -m pip install --upgrade subreel` dentro do ambiente virtual e
verifique a conexão com a internet: Edge TTS precisa acessar o serviço online.
Confira também se o texto da narração não está vazio e se o ambiente virtual
correto está ativo.

### Render HyperFrames falha

Confirme `node --version` e `npm --version`, reinicie o terminal após instalar
Node.js e tente novamente. O primeiro render pode precisar baixar o CLI
HyperFrames via npm, portanto requer acesso à internet.

## Amostras

As descrições e os vídeos de referência ficam em `samples/`. As notas em
`samples/QUALITY_NOTES.md` registram os resultados técnicos e identificam
quais aspectos de voz e sincronização ainda precisam de escuta/revisão humana.

# Notas de qualidade das amostras

As cinco descrições em português estão acompanhadas por exports verticais em
1080x1920, H.264/yuv420p e AAC. Cada vídeo deve ser conferido junto à sua
descrição e narração correspondente.

## Critérios objetivos

- Resolução e codecs são verificados por `ffprobe`.
- A faixa de narração é gerada pelo `subreel`/Edge TTS e incorporada na
  exportação.
- Os tempos por palavra de `voice.words.json` alimentam as legendas ASS; a
  composição usa a duração da última palavra mais 0,3 s de margem.
- A geração dos arquivos, por si só, não garante que a fala soe natural nem
  substitui uma revisão visual/auditiva do sincronismo.

## Avaliação subjetiva — revisão humana pendente

| Amostra | Naturalidade da voz pt-BR | Sincronismo das legendas | Ação |
|---|---|---|---|
| 01 — Hidratação (3,63 s) | Não avaliada por escuta humana | Conferir reprodução do início ao fim | Não decidir troca de TTS antes da escuta |
| 02 — Respiração (5,87 s) | Não avaliada por escuta humana | Conferir reprodução do início ao fim | Não decidir troca de TTS antes da escuta |
| 03 — Café da manhã (10,67 s) | Não avaliada por escuta humana | Conferir reprodução do início ao fim | Não decidir troca de TTS antes da escuta |
| 04 — Organização (3,23 s) | Não avaliada por escuta humana | Conferir reprodução do início ao fim | Não decidir troca de TTS antes da escuta |
| 05 — Natureza (4,10 s) | Não avaliada por escuta humana | Conferir reprodução do início ao fim | Não decidir troca de TTS antes da escuta |

**Gate de qualidade:** inconclusivo. Os artefatos e timings podem ser
validados automaticamente, mas a naturalidade e a percepção do alinhamento
precisam ser julgadas ouvindo e assistindo aos cinco vídeos. Não há evidência
suficiente para afirmar que a voz atual é aceitável ou que precisa ser trocada.

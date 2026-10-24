# Animações suportadas

Mapeamento de `data-animation` para receitas GSAP do HyperFrames.

| data-animation | Efeito | Primitiva HyperFrames |
|---|---|---|
| `fade-in` | Aparece suavemente | `fade_in` |
| `slide-up` | Sobe de baixo | `slide_bottom` |
| `slide-left` | Vem da esquerda | `slide_left` |
| `scale-in` | Cresce do zero | `scale_grow` |
| `typewriter` | Revela como máquina de escrever | `typewriter` |

## Como usar

No HTML da composição:
```html
<div class="clip" data-animation="slide-up" data-start="0" data-duration="3">...</div>
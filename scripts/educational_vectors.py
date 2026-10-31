"""Biblioteca abrangente de ilustrações vetoriais em Motion Design (SVG) para Vestibular e Concursos Públicos.

Cobre todo o currículo de ENEM, Vestibulares tradicionais (FUVEST, UNICAMP) e Concursos Públicos:
- Língua Portuguesa & Redação
- Direito Constitucional & Administrativo
- Raciocínio Lógico & Matemática (RLM)
- Física, Química & Biologia
- História & Geografia
"""

import html
import re
from typing import Any

# ==============================================================================
# ILUSTRAÇÕES VETORIAIS (SVGs PROFISSIONAIS EM MOTION DESIGN)
# ==============================================================================

def svg_law_constitution() -> str:
    """Balança da Justiça, Colunas do Estado de Direito & CF/88."""
    return '''
    <div class="bio-vector-stage">
      <svg class="law-justice-svg" viewBox="0 0 460 170" width="100%" height="170">
        <defs>
          <filter id="justiceGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feComposite in="SourceGraphic" in2="blur" operator="over"/>
          </filter>
        </defs>
        <!-- Pilar Central da Justiça -->
        <line x1="230" y1="35" x2="230" y2="145" stroke="var(--palettePrimary)" stroke-width="4" stroke-linecap="round"/>
        <circle cx="230" cy="35" r="10" fill="var(--paletteAccent)" filter="url(#justiceGlow)"/>
        <!-- Haste Horizontal da Balança (Oscilante) -->
        <g class="balance-beam" transform-origin="230 45">
          <line x1="140" y1="45" x2="320" y2="45" stroke="var(--palettePrimary)" stroke-width="3" stroke-linecap="round"/>
          <circle cx="140" cy="45" r="4" fill="#ffffff"/>
          <circle cx="320" cy="45" r="4" fill="#ffffff"/>
          <!-- Prato Esquerdo: Legalidade / CF/88 -->
          <line x1="140" y1="45" x2="120" y2="95" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
          <line x1="140" y1="45" x2="160" y2="95" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
          <path d="M 110 95 Q 140 115 170 95 Z" fill="rgba(56, 189, 248, 0.2)" stroke="var(--palettePrimary)" stroke-width="2"/>
          <text x="140" y="85" fill="#38bdf8" font-size="9" font-weight="800" text-anchor="middle">LEI</text>
          <!-- Prato Direito: Direitos Fundamentais -->
          <line x1="320" y1="45" x2="300" y2="95" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
          <line x1="320" y1="45" x2="340" y2="95" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
          <path d="M 290 95 Q 320 115 350 95 Z" fill="rgba(168, 85, 247, 0.2)" stroke="var(--paletteAccent)" stroke-width="2"/>
          <text x="320" y="85" fill="#c084fc" font-size="9" font-weight="800" text-anchor="middle">DIREITOS</text>
        </g>
        <!-- Base Sólida do Estado de Direito -->
        <rect x="180" y="145" width="100" height="12" rx="4" fill="rgba(255,255,255,0.1)" stroke="var(--palettePrimary)" stroke-width="1.5"/>
        <text x="230" y="154" fill="#ffffff" font-size="8" font-weight="800" text-anchor="middle" letter-spacing="1">ESTADO DEMOCRÁTICO</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> DIREITO CONSTITUCIONAL // CF/88 & ESTADO DE DIREITO
      </div>
    </div>'''


def svg_law_limpe() -> str:
    """Princípios da Administração Pública (L.I.M.P.E. - Art. 37 CF/88)."""
    return '''
    <div class="bio-vector-stage">
      <svg class="law-limpe-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Escudo Central da Administração -->
        <path d="M 230 25 L 285 45 L 285 95 Q 230 145 230 145 Q 175 95 175 95 L 175 45 Z"
              fill="rgba(56, 189, 248, 0.08)" stroke="var(--palettePrimary)" stroke-width="2.5"/>
        <text x="230" y="85" fill="#ffffff" font-size="14" font-weight="900" text-anchor="middle">L.I.M.P.E.</text>
        <text x="230" y="102" fill="var(--paletteAccent)" font-size="9" font-weight="700" text-anchor="middle">ART. 37 CF/88</text>
        <!-- 5 Selos Orbitais dos Princípios -->
        <g class="limpe-badge lb-1" transform="translate(90, 50)">
          <circle cx="0" cy="0" r="22" fill="rgba(6, 182, 212, 0.15)" stroke="#06b6d4" stroke-width="1.8"/>
          <text x="0" y="4" fill="#ffffff" font-size="9" font-weight="800" text-anchor="middle">LEGAL</text>
        </g>
        <g class="limpe-badge lb-2" transform="translate(90, 115)">
          <circle cx="0" cy="0" r="22" fill="rgba(168, 85, 247, 0.15)" stroke="#a855f7" stroke-width="1.8"/>
          <text x="0" y="4" fill="#ffffff" font-size="8" font-weight="800" text-anchor="middle">IMPESSOAL</text>
        </g>
        <g class="limpe-badge lb-3" transform="translate(370, 50)">
          <circle cx="0" cy="0" r="22" fill="rgba(245, 158, 11, 0.15)" stroke="#f59e0b" stroke-width="1.8"/>
          <text x="0" y="4" fill="#ffffff" font-size="8.5" font-weight="800" text-anchor="middle">MORAL</text>
        </g>
        <g class="limpe-badge lb-4" transform="translate(370, 115)">
          <circle cx="0" cy="0" r="22" fill="rgba(16, 185, 129, 0.15)" stroke="#10b981" stroke-width="1.8"/>
          <text x="0" y="4" fill="#ffffff" font-size="8" font-weight="800" text-anchor="middle">PÚBLICO</text>
        </g>
        <!-- Linhas conectoras com a Administração -->
        <line x1="112" y1="50" x2="175" y2="65" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" stroke-dasharray="3 3"/>
        <line x1="112" y1="115" x2="185" y2="105" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" stroke-dasharray="3 3"/>
        <line x1="348" y1="50" x2="285" y2="65" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" stroke-dasharray="3 3"/>
        <line x1="348" y1="115" x2="275" y2="105" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" stroke-dasharray="3 3"/>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> DIREITO ADMINISTRATIVO // PRINCÍPIOS CONSTITUCIONAIS
      </div>
    </div>'''


def svg_logic_venn() -> str:
    """Raciocínio Lógico: Diagramas de Venn, Teoria dos Conjuntos & Conectivos."""
    return '''
    <div class="bio-vector-stage">
      <svg class="logic-venn-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Universo de Discurso -->
        <rect x="50" y="25" width="360" height="120" rx="12" fill="rgba(255,255,255,0.02)" stroke="rgba(255,255,255,0.15)" stroke-width="1.5"/>
        <text x="65" y="42" fill="#94a3b8" font-size="10" font-weight="800">UNIVERSO (U)</text>
        <!-- Conjunto A -->
        <circle class="venn-circle set-a" cx="190" cy="85" r="50" fill="rgba(56, 189, 248, 0.12)" stroke="var(--palettePrimary)" stroke-width="2.5"/>
        <text x="160" y="88" fill="#38bdf8" font-size="14" font-weight="900">A</text>
        <!-- Conjunto B -->
        <circle class="venn-circle set-b" cx="270" cy="85" r="50" fill="rgba(168, 85, 247, 0.12)" stroke="var(--paletteAccent)" stroke-width="2.5"/>
        <text x="300" y="88" fill="#c084fc" font-size="14" font-weight="900">B</text>
        <!-- Intersecção A ∩ B -->
        <path d="M 230 46 A 50 50 0 0 1 230 124 A 50 50 0 0 1 230 46 Z" fill="rgba(16, 185, 129, 0.35)" stroke="#10b981" stroke-width="2"/>
        <text x="230" y="88" fill="#ffffff" font-size="10" font-weight="900" text-anchor="middle">A ∩ B</text>
        <!-- Conectivos Lógicos Badge -->
        <g transform="translate(350, 40)">
          <text x="0" y="0" fill="#38bdf8" font-size="9" font-weight="700">∧ (E): Intersecção</text>
          <text x="0" y="15" fill="#c084fc" font-size="9" font-weight="700">∨ (OU): União</text>
          <text x="0" y="30" fill="#10b981" font-size="9" font-weight="700">→ : Condicional</text>
        </g>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> RACIOCÍNIO LÓGICO (RLM) // DIAGRAMAS DE VENN
      </div>
    </div>'''


def svg_logic_truth_table() -> str:
    """Lógica Proposicional: Tabela-Verdade e Valoração."""
    return '''
    <div class="bio-vector-stage">
      <svg class="logic-table-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Placa da Tabela-Verdade -->
        <rect x="80" y="25" width="300" height="120" rx="10" fill="rgba(6, 14, 28, 0.85)" stroke="var(--palettePrimary)" stroke-width="2"/>
        <!-- Cabeçalho -->
        <line x1="80" y1="55" x2="380" y2="55" stroke="var(--palettePrimary)" stroke-width="1.5"/>
        <line x1="170" y1="25" x2="170" y2="145" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
        <line x1="260" y1="25" x2="260" y2="145" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
        <text x="125" y="45" fill="var(--palettePrimary)" font-size="12" font-weight="900" text-anchor="middle">P</text>
        <text x="215" y="45" fill="var(--palettePrimary)" font-size="12" font-weight="900" text-anchor="middle">Q</text>
        <text x="320" y="45" fill="var(--paletteAccent)" font-size="12" font-weight="900" text-anchor="middle">P → Q (Se... Então)</text>
        <!-- Linhas com LEDs de V/F -->
        <text x="125" y="75" fill="#10b981" font-size="11" font-weight="800" text-anchor="middle">V</text>
        <text x="215" y="75" fill="#10b981" font-size="11" font-weight="800" text-anchor="middle">V</text>
        <text x="320" y="75" fill="#10b981" font-size="11" font-weight="900" text-anchor="middle">V (Verdade)</text>

        <text x="125" y="98" fill="#10b981" font-size="11" font-weight="800" text-anchor="middle">V</text>
        <text x="215" y="98" fill="#ef4444" font-size="11" font-weight="800" text-anchor="middle">F</text>
        <text x="320" y="98" fill="#ef4444" font-size="11" font-weight="900" text-anchor="middle">F (Falso: Vera Fischer)</text>

        <text x="125" y="122" fill="#ef4444" font-size="11" font-weight="800" text-anchor="middle">F</text>
        <text x="215" y="122" fill="#10b981" font-size="11" font-weight="800" text-anchor="middle">V</text>
        <text x="320" y="122" fill="#10b981" font-size="11" font-weight="900" text-anchor="middle">V (Verdade)</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> LÓGICA PROPOSICIONAL // CONDICIONAL & TABELA-VERDADE
      </div>
    </div>'''


def svg_grammar_syntax() -> str:
    """Árvore Sintática da Língua Portuguesa (Termos Essenciais & Integrantes)."""
    return '''
    <div class="bio-vector-stage">
      <svg class="syntax-tree-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Nó Central: Oração -->
        <rect x="180" y="20" width="100" height="28" rx="6" fill="rgba(56, 189, 248, 0.15)" stroke="var(--palettePrimary)" stroke-width="2"/>
        <text x="230" y="38" fill="#ffffff" font-size="11" font-weight="900" text-anchor="middle">ORAÇÃO</text>
        <!-- Ramificação: Sujeito & Predicado -->
        <path d="M 230 48 L 130 75 M 230 48 L 330 75" stroke="var(--palettePrimary)" stroke-width="2"/>
        <rect x="75" y="75" width="110" height="26" rx="6" fill="rgba(168, 85, 247, 0.15)" stroke="var(--paletteAccent)" stroke-width="1.8"/>
        <text x="130" y="92" fill="#c084fc" font-size="10" font-weight="800" text-anchor="middle">SUJEITO</text>

        <rect x="275" y="75" width="110" height="26" rx="6" fill="rgba(16, 185, 129, 0.15)" stroke="#10b981" stroke-width="1.8"/>
        <text x="330" y="92" fill="#86efac" font-size="10" font-weight="800" text-anchor="middle">PREDICADO</text>
        <!-- Ramificação do Predicado: Verbo Transitivo & Complemento -->
        <path d="M 330 101 L 275 125 M 330 101 L 385 125" stroke="#10b981" stroke-width="1.8"/>
        <rect x="235" y="125" width="80" height="24" rx="4" fill="rgba(255,255,255,0.06)" stroke="#10b981" stroke-width="1.2"/>
        <text x="275" y="141" fill="#ffffff" font-size="9" font-weight="700" text-anchor="middle">VTD / VTI</text>

        <rect x="345" y="125" width="80" height="24" rx="4" fill="rgba(255,255,255,0.06)" stroke="#10b981" stroke-width="1.2"/>
        <text x="385" y="141" fill="#ffffff" font-size="9" font-weight="700" text-anchor="middle">OBJETO (OD/OI)</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> SINTAXE DA LÍNGUA PORTUGUESA // ANÁLISE ESTRUTURAL
      </div>
    </div>'''


def svg_redacao_enem() -> str:
    """Estrutura da Redação Nota 1000 (ENEM & Concursos)."""
    return '''
    <div class="bio-vector-stage">
      <svg class="redacao-enem-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- 4 Pilares da Redação -->
        <g class="red-block rb-1" transform="translate(60, 30)">
          <rect x="0" y="0" width="75" height="90" rx="8" fill="rgba(56, 189, 248, 0.1)" stroke="var(--palettePrimary)" stroke-width="1.8"/>
          <text x="37" y="25" fill="var(--palettePrimary)" font-size="10" font-weight="900" text-anchor="middle">INTRO</text>
          <text x="37" y="50" fill="#ffffff" font-size="8" font-weight="700" text-anchor="middle">Tese</text>
          <text x="37" y="65" fill="#94a3b8" font-size="8" text-anchor="middle">Repertório</text>
        </g>
        <line x1="140" y1="75" x2="160" y2="75" stroke="var(--palettePrimary)" stroke-width="2" marker-end="url(#arrow)"/>
        <g class="red-block rb-2" transform="translate(165, 30)">
          <rect x="0" y="0" width="75" height="90" rx="8" fill="rgba(168, 85, 247, 0.1)" stroke="var(--paletteAccent)" stroke-width="1.8"/>
          <text x="37" y="25" fill="var(--paletteAccent)" font-size="10" font-weight="900" text-anchor="middle">DESENV. 1</text>
          <text x="37" y="50" fill="#ffffff" font-size="8" font-weight="700" text-anchor="middle">Causa</text>
          <text x="37" y="65" fill="#94a3b8" font-size="8" text-anchor="middle">Dado/Fato</text>
        </g>
        <line x1="245" y1="75" x2="265" y2="75" stroke="var(--paletteAccent)" stroke-width="2"/>
        <g class="red-block rb-3" transform="translate(270, 30)">
          <rect x="0" y="0" width="75" height="90" rx="8" fill="rgba(168, 85, 247, 0.1)" stroke="var(--paletteAccent)" stroke-width="1.8"/>
          <text x="37" y="25" fill="var(--paletteAccent)" font-size="10" font-weight="900" text-anchor="middle">DESENV. 2</text>
          <text x="37" y="50" fill="#ffffff" font-size="8" font-weight="700" text-anchor="middle">Efeito</text>
          <text x="37" y="65" fill="#94a3b8" font-size="8" text-anchor="middle">Filósofo</text>
        </g>
        <line x1="350" y1="75" x2="370" y2="75" stroke="#10b981" stroke-width="2"/>
        <g class="red-block rb-4" transform="translate(375, 30)">
          <rect x="0" y="0" width="70" height="90" rx="8" fill="rgba(16, 185, 129, 0.12)" stroke="#10b981" stroke-width="2"/>
          <text x="35" y="25" fill="#10b981" font-size="9" font-weight="900" text-anchor="middle">PROPOSTA</text>
          <text x="35" y="45" fill="#86efac" font-size="7.5" font-weight="700" text-anchor="middle">Agente</text>
          <text x="35" y="58" fill="#86efac" font-size="7.5" font-weight="700" text-anchor="middle">Ação</text>
          <text x="35" y="71" fill="#86efac" font-size="7.5" font-weight="700" text-anchor="middle">Meio/Modo</text>
        </g>
        <!-- Selo Nota 1000 -->
        <rect x="160" y="132" width="140" height="22" rx="11" fill="rgba(245, 158, 11, 0.15)" stroke="#f59e0b" stroke-width="1.5"/>
        <text x="230" y="147" fill="#fef08a" font-size="9" font-weight="900" text-anchor="middle">★ NOTA 1000 // 5 COMPETÊNCIAS</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> REDAÇÃO ENEM & CONCURSOS // ESTRUTURA DISSERTATIVA
      </div>
    </div>'''


def svg_math_cartesian() -> str:
    """Funções, Gráfico Cartesiano & Parábola (ENEM / Matemática)."""
    return '''
    <div class="bio-vector-stage">
      <svg class="math-cartesian-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Eixos Cartesianos -->
        <line x1="80" y1="135" x2="380" y2="135" stroke="rgba(255,255,255,0.4)" stroke-width="2"/>
        <line x1="160" y1="20" x2="160" y2="150" stroke="rgba(255,255,255,0.4)" stroke-width="2"/>
        <text x="375" y="125" fill="#94a3b8" font-size="10" font-weight="800">X</text>
        <text x="170" y="30" fill="#94a3b8" font-size="10" font-weight="800">Y</text>
        <!-- Curva da Parábola (Função de 2º Grau com Vértice) -->
        <path class="parabola-curve" d="M 100 35 Q 230 185 360 35" fill="none" stroke="var(--palettePrimary)" stroke-width="3" stroke-linecap="round"/>
        <!-- Raízes X1 e X2 -->
        <circle cx="140" cy="135" r="5" fill="var(--paletteAccent)"/>
        <text x="140" y="152" fill="var(--paletteAccent)" font-size="10" font-weight="800" text-anchor="middle">x₁</text>
        <circle cx="320" cy="135" r="5" fill="var(--paletteAccent)"/>
        <text x="320" y="152" fill="var(--paletteAccent)" font-size="10" font-weight="800" text-anchor="middle">x₂</text>
        <!-- Vértice V (xv, yv) -->
        <circle cx="230" cy="110" r="5" fill="#ef4444"/>
        <line x1="230" y1="110" x2="230" y2="135" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="3 3"/>
        <text x="230" y="100" fill="#fca5a5" font-size="9" font-weight="800" text-anchor="middle">Vértice (Mínimo)</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> MATEMÁTICA // FUNÇÃO QUADRÁTICA & VÉRTICE
      </div>
    </div>'''


def svg_physics_mechanics() -> str:
    """Física: Mecânica Clássica, Plano Inclinado & Leis de Newton."""
    return '''
    <div class="bio-vector-stage">
      <svg class="physics-mechanics-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Rampa do Plano Inclinado -->
        <path d="M 80 140 L 360 140 L 360 40 Z" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.3)" stroke-width="2"/>
        <path d="M 120 140 A 40 40 0 0 0 115 125" fill="none" stroke="var(--paletteAccent)" stroke-width="2"/>
        <text x="130" y="135" fill="var(--paletteAccent)" font-size="10" font-weight="800">θ</text>
        <!-- Bloco de Massa M sobre a rampa -->
        <g transform="translate(230, 92) rotate(-20)">
          <rect x="-22" y="-18" width="44" height="36" rx="4" fill="rgba(56, 189, 248, 0.25)" stroke="var(--palettePrimary)" stroke-width="2"/>
          <text x="0" y="5" fill="#ffffff" font-size="12" font-weight="900" text-anchor="middle">m</text>
          <!-- Vetor Força Normal N -->
          <line x1="0" y1="-18" x2="0" y2="-55" stroke="#10b981" stroke-width="2.5" stroke-linecap="round"/>
          <text x="8" y="-45" fill="#10b981" font-size="9" font-weight="800">N</text>
          <!-- Vetor Força de Atrito Fat -->
          <line x1="22" y1="18" x2="55" y2="18" stroke="#f59e0b" stroke-width="2.5" stroke-linecap="round"/>
          <text x="60" y="22" fill="#f59e0b" font-size="9" font-weight="800">Fat</text>
        </g>
        <!-- Vetor Força Peso P (vertical para baixo) -->
        <line x1="230" y1="92" x2="230" y2="155" stroke="#ef4444" stroke-width="3" stroke-linecap="round"/>
        <text x="240" y="150" fill="#ef4444" font-size="10" font-weight="900">P = m·g</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> FÍSICA MECÂNICA // PLANO INCLINADO & FORÇAS DE NEWTON
      </div>
    </div>'''


def svg_physics_circuits() -> str:
    """Física: Eletrodinâmica, Circuitos & 1ª Lei de Ohm (V = R * i)."""
    return '''
    <div class="bio-vector-stage">
      <svg class="physics-circuits-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Linha do Circuito Fechado -->
        <rect x="90" y="35" width="280" height="100" rx="10" fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="2.5"/>
        <!-- Gerador / Bateria DC (+ / -) -->
        <line x1="90" y1="75" x2="90" y2="95" stroke="#ef4444" stroke-width="4"/>
        <line x1="90" y1="80" x2="90" y2="90" stroke="#38bdf8" stroke-width="2"/>
        <text x="65" y="88" fill="#ef4444" font-size="12" font-weight="900">U (V)</text>
        <!-- Resistor R em Zigue-Zague -->
        <path d="M 200 35 L 210 23 L 220 47 L 230 23 L 240 47 L 250 23 L 260 35"
              fill="none" stroke="var(--paletteAccent)" stroke-width="3.5" stroke-linejoin="round"/>
        <text x="230" y="18" fill="var(--paletteAccent)" font-size="11" font-weight="900" text-anchor="middle">RESISTOR (R)</text>
        <!-- Elétrons em movimento com corrente i -->
        <circle class="circuit-electron ce-1" cx="150" cy="35" r="4" fill="#fef08a"/>
        <circle class="circuit-electron ce-2" cx="310" cy="35" r="4" fill="#fef08a"/>
        <circle class="circuit-electron ce-3" cx="370" cy="85" r="4" fill="#fef08a"/>
        <circle class="circuit-electron ce-4" cx="230" cy="135" r="4" fill="#fef08a"/>
        <!-- Fórmula de Ohm -->
        <rect x="180" y="85" width="100" height="24" rx="6" fill="rgba(16, 185, 129, 0.15)" stroke="#10b981" stroke-width="1.5"/>
        <text x="230" y="101" fill="#86efac" font-size="11" font-weight="900" text-anchor="middle">U = R · i</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> ELETRODINÂMICA // CIRCUITO & 1ª LEI DE OHM
      </div>
    </div>'''


def svg_chemistry_organic() -> str:
    """Química Orgânica: Anel Benzênico, Cadeias Carbônicas & Funções."""
    return '''
    <div class="bio-vector-stage">
      <svg class="chem-organic-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Anel Aromático do Benzeno (Hexágono com Ressonância) -->
        <g class="benzene-ring" transform="translate(180, 85)">
          <polygon points="0,-45 39,-22.5 39,22.5 0,45 -39,22.5 -39,-22.5"
                   fill="rgba(56, 189, 248, 0.08)" stroke="var(--palettePrimary)" stroke-width="3"/>
          <circle cx="0" cy="0" r="26" fill="none" stroke="var(--paletteAccent)" stroke-width="2" stroke-dasharray="6 4"/>
        </g>
        <!-- Radical Funcional Ligado (Hidroxila OH / Fenol) -->
        <line x1="219" y1="62.5" x2="265" y2="40" stroke="var(--palettePrimary)" stroke-width="3"/>
        <text x="275" y="44" fill="#ef4444" font-size="14" font-weight="900">OH</text>
        <text x="275" y="58" fill="#fca5a5" font-size="9" font-weight="700">FENOL</text>
        <!-- Radical Alquila (CH3 / Tolueno) -->
        <line x1="180" y1="130" x2="180" y2="155" stroke="var(--palettePrimary)" stroke-width="3"/>
        <text x="180" y="166" fill="#38bdf8" font-size="11" font-weight="800" text-anchor="middle">CH₃</text>
        <!-- Telemetria de Ressonância -->
        <text x="350" y="80" fill="var(--paletteAccent)" font-size="11" font-weight="800">RESSONÂNCIA</text>
        <text x="350" y="96" fill="#94a3b8" font-size="9">Elétrons π Deslocalizados</text>
        <text x="350" y="110" fill="#10b981" font-size="9" font-weight="700">C₆H₆ (ESTÁVEL)</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> QUÍMICA ORGÂNICA // ANEL AROMÁTICO & HIDROCARBONETOS
      </div>
    </div>'''


def svg_chemistry_reaction() -> str:
    """Química Geral: Termoquímica, pH & Cinética Química."""
    return '''
    <div class="bio-vector-stage">
      <svg class="chem-reaction-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Balão de Erlenmeyer com Reação -->
        <path d="M 175 40 L 195 40 L 195 70 L 155 135 A 8 8 0 0 0 162 145 L 238 145 A 8 8 0 0 0 245 135 L 205 70 L 205 40 L 225 40"
              fill="rgba(56, 189, 248, 0.06)" stroke="var(--palettePrimary)" stroke-width="2.5"/>
        <!-- Líquido com indicador de pH -->
        <path d="M 166 115 L 234 115 L 243 133 A 8 8 0 0 1 236 143 L 164 143 A 8 8 0 0 1 157 133 Z"
              fill="rgba(168, 85, 247, 0.45)"/>
        <!-- Bolhas e vapores de reação -->
        <circle class="chem-bubble cb1" cx="190" cy="125" r="3" fill="#ffffff"/>
        <circle class="chem-bubble cb2" cx="210" cy="120" r="3.5" fill="#ffffff"/>
        <circle class="chem-bubble cb3" cx="200" cy="135" r="2.5" fill="#ffffff"/>
        <!-- Escala de pH Lateral -->
        <g transform="translate(300, 40)">
          <text x="0" y="10" fill="#ffffff" font-size="11" font-weight="800">POTENCIAL pH</text>
          <rect x="0" y="20" width="120" height="14" rx="4" fill="url(#phGradient)" stroke="rgba(255,255,255,0.2)"/>
          <text x="0" y="48" fill="#ef4444" font-size="9" font-weight="700">ÁCIDO (1-6)</text>
          <text x="50" y="48" fill="#10b981" font-size="9" font-weight="700">NEUTRO (7)</text>
          <text x="100" y="48" fill="#818cf8" font-size="9" font-weight="700">BASE</text>
        </g>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> FÍSICO-QUÍMICA // ESCALA DE pH & REAÇÃO
      </div>
    </div>'''


def svg_bio_ecology() -> str:
    """Biologia: Ecologia, Pirâmide Trófica & Cadeia Alimentar."""
    return '''
    <div class="bio-vector-stage">
      <svg class="bio-ecology-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Pirâmide de Energia em Níveis Tróficos -->
        <!-- Nível 3: Consumidores Secundários / Topo -->
        <polygon points="230,30 190,65 270,65" fill="rgba(239, 68, 68, 0.3)" stroke="#ef4444" stroke-width="2"/>
        <text x="230" y="55" fill="#fca5a5" font-size="8.5" font-weight="800" text-anchor="middle">TOPO (10 kcal)</text>

        <!-- Nível 2: Consumidores Primários (Herbívoros) -->
        <polygon points="190,65 270,65 305,100 155,100" fill="rgba(245, 158, 11, 0.3)" stroke="#f59e0b" stroke-width="2"/>
        <text x="230" y="88" fill="#fef08a" font-size="9" font-weight="800" text-anchor="middle">HERBÍVOROS (100 kcal)</text>

        <!-- Nível 1: Produtores (Autótrofos / Base) -->
        <polygon points="155,100 305,100 340,140 120,140" fill="rgba(16, 185, 129, 0.35)" stroke="#10b981" stroke-width="2"/>
        <text x="230" y="125" fill="#bbf7d0" font-size="10" font-weight="900" text-anchor="middle">PRODUTORES // FOTOSSÍNTESE (1.000 kcal)</text>

        <!-- Seta de Fluxo Unidirecional de Energia -->
        <path d="M 370 135 L 370 40" stroke="var(--palettePrimary)" stroke-width="2.5" marker-end="url(#arrow)" stroke-dasharray="4 3"/>
        <text x="378" y="85" fill="var(--palettePrimary)" font-size="8.5" font-weight="800">FLUXO DE ENERGIA (DECRESCENTE)</text>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> ECOLOGIA // PIRÂMIDE TRÓFICA & CADEIA ALIMENTAR
      </div>
    </div>'''


def svg_bio_neuron() -> str:
    """Fisiologia: Neurônio, Sinapse & Potencial de Ação."""
    return '''
    <div class="bio-vector-stage">
      <svg class="bio-neuron-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Corpo Celular (Soma) e Dendritos -->
        <polygon points="100,85 75,55 60,70 70,85 55,100 75,115 100,85" fill="rgba(56, 189, 248, 0.25)" stroke="var(--palettePrimary)" stroke-width="2"/>
        <circle cx="85" cy="85" r="10" fill="var(--paletteAccent)"/>
        <!-- Axônio com Bainha de Mielina -->
        <line x1="100" y1="85" x2="350" y2="85" stroke="#ffffff" stroke-width="2"/>
        <rect x="130" y="74" width="38" height="22" rx="6" fill="rgba(245, 158, 11, 0.3)" stroke="#f59e0b" stroke-width="1.8"/>
        <rect x="185" y="74" width="38" height="22" rx="6" fill="rgba(245, 158, 11, 0.3)" stroke="#f59e0b" stroke-width="1.8"/>
        <rect x="240" y="74" width="38" height="22" rx="6" fill="rgba(245, 158, 11, 0.3)" stroke="#f59e0b" stroke-width="1.8"/>
        <rect x="295" y="74" width="38" height="22" rx="6" fill="rgba(245, 158, 11, 0.3)" stroke="#f59e0b" stroke-width="1.8"/>
        <!-- Impulso Nervoso / Sinapse -->
        <circle class="action-potential" cx="215" cy="85" r="5" fill="#38bdf8"/>
        <text x="215" y="60" fill="#38bdf8" font-size="9" font-weight="800" text-anchor="middle">IMPULSO SALTATÓRIO</text>
        <!-- Botão Sináptico -->
        <circle cx="365" cy="70" r="6" fill="#10b981"/>
        <circle cx="365" cy="100" r="6" fill="#10b981"/>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> FISIOLOGIA HUMANA // NEURÔNIO & SINAPSE
      </div>
    </div>'''


def svg_history_brazil() -> str:
    """Historiografia do Brasil & Geral: Linha do Tempo e Eras."""
    return '''
    <div class="bio-vector-stage">
      <svg class="history-brazil-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Trilho Temporal Luminoso -->
        <line x1="60" y1="85" x2="400" y2="85" stroke="var(--palettePrimary)" stroke-width="3"/>
        <!-- Marcos Históricos -->
        <g class="hist-node hn-1" transform="translate(90, 85)">
          <circle cx="0" cy="0" r="14" fill="rgba(56, 189, 248, 0.25)" stroke="var(--palettePrimary)" stroke-width="2"/>
          <circle cx="0" cy="0" r="5" fill="var(--palettePrimary)"/>
          <text x="0" y="-22" fill="#ffffff" font-size="9" font-weight="900" text-anchor="middle">1500</text>
          <text x="0" y="28" fill="#94a3b8" font-size="8.5" font-weight="700" text-anchor="middle">COLÔNIA</text>
        </g>
        <g class="hist-node hn-2" transform="translate(190, 85)">
          <circle cx="0" cy="0" r="14" fill="rgba(245, 158, 11, 0.25)" stroke="#f59e0b" stroke-width="2"/>
          <circle cx="0" cy="0" r="5" fill="#f59e0b"/>
          <text x="0" y="-22" fill="#ffffff" font-size="9" font-weight="900" text-anchor="middle">1822</text>
          <text x="0" y="28" fill="#94a3b8" font-size="8.5" font-weight="700" text-anchor="middle">IMPÉRIO</text>
        </g>
        <g class="hist-node hn-3" transform="translate(290, 85)">
          <circle cx="0" cy="0" r="14" fill="rgba(168, 85, 247, 0.25)" stroke="var(--paletteAccent)" stroke-width="2"/>
          <circle cx="0" cy="0" r="5" fill="var(--paletteAccent)"/>
          <text x="0" y="-22" fill="#ffffff" font-size="9" font-weight="900" text-anchor="middle">1889</text>
          <text x="0" y="28" fill="#94a3b8" font-size="8.5" font-weight="700" text-anchor="middle">REPÚBLICA</text>
        </g>
        <g class="hist-node hn-4" transform="translate(380, 85)">
          <circle cx="0" cy="0" r="16" fill="rgba(16, 185, 129, 0.35)" stroke="#10b981" stroke-width="2.5"/>
          <circle cx="0" cy="0" r="6" fill="#10b981"/>
          <text x="0" y="-24" fill="#86efac" font-size="9" font-weight="900" text-anchor="middle">1988</text>
          <text x="0" y="30" fill="#86efac" font-size="8.5" font-weight="800" text-anchor="middle">CF CIDADÃ</text>
        </g>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> HISTÓRIA & CRONOLOGIA // MARCOS INSTITUCIONAIS
      </div>
    </div>'''


def svg_geo_plates() -> str:
    """Geografia Física: Tectônica de Placas, Relevo & Camadas da Terra."""
    return '''
    <div class="bio-vector-stage">
      <svg class="geo-plates-svg" viewBox="0 0 460 170" width="100%" height="170">
        <!-- Camada da Crosta e Manto -->
        <rect x="70" y="115" width="320" height="35" fill="rgba(245, 158, 11, 0.2)" stroke="#f59e0b" stroke-width="1.5"/>
        <text x="230" y="136" fill="#fef08a" font-size="9" font-weight="800" text-anchor="middle">MANTO SUPERIOR // ASTENOSFERA (MAGMA)</text>
        <!-- Placa A e Placa B convergindo -->
        <path d="M 80 115 L 210 115 L 210 95 L 80 95 Z" fill="rgba(56, 189, 248, 0.25)" stroke="var(--palettePrimary)" stroke-width="2"/>
        <text x="145" y="108" fill="#ffffff" font-size="9" font-weight="800" text-anchor="middle">PLACA SUL-AMERICANA</text>
        <!-- Zona de Subducção e Formação de Montanhas -->
        <polygon points="210,95 240,45 270,95" fill="rgba(16, 185, 129, 0.3)" stroke="#10b981" stroke-width="2"/>
        <text x="240" y="75" fill="#86efac" font-size="8.5" font-weight="800" text-anchor="middle">OROGÊNESE</text>
        <path d="M 270 95 L 380 95 L 380 115 L 245 115 Z" fill="rgba(168, 85, 247, 0.25)" stroke="var(--paletteAccent)" stroke-width="2"/>
        <!-- Setas de Convergência -->
        <line x1="120" y1="80" x2="170" y2="80" stroke="var(--palettePrimary)" stroke-width="2.5" marker-end="url(#arrow)"/>
        <line x1="340" y1="80" x2="290" y2="80" stroke="var(--paletteAccent)" stroke-width="2.5" marker-end="url(#arrow)"/>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> GEOGRAFIA FÍSICA // TECTÔNICA DE PLACAS & RELEVO
      </div>
    </div>'''


def svg_bio_tissue() -> str:
    """Histologia Humana: Tecido Conjuntivo, Matriz Extracelular, Colágeno, Fibras e Células."""
    return '''
    <div class="bio-vector-stage">
      <svg class="bio-tissue-svg" viewBox="0 0 460 170" width="100%" height="170">
        <defs>
          <linearGradient id="collagenGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="var(--palettePrimary)" stop-opacity="0.9"/>
            <stop offset="50%" stop-color="#38bdf8" stop-opacity="0.95"/>
            <stop offset="100%" stop-color="var(--paletteAccent)" stop-opacity="0.9"/>
          </linearGradient>
          <filter id="tissueGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feComposite in="SourceGraphic" in2="blur" operator="over"/>
          </filter>
        </defs>

        <!-- Matriz Extracelular (Substância Fundamental Amorfa) -->
        <rect x="50" y="20" width="360" height="130" rx="14" fill="rgba(56, 189, 248, 0.04)" stroke="rgba(56, 189, 248, 0.2)" stroke-width="1.5"/>
        <text x="65" y="38" fill="#94a3b8" font-size="9" font-weight="800" letter-spacing="1">MATRIZ EXTRACELULAR (MEC)</text>

        <!-- Feixes de Fibras Colágenas (Resistência e Sustentação) -->
        <path d="M 60 70 Q 140 45, 220 75 T 400 65" fill="none" stroke="url(#collagenGrad)" stroke-width="4.5" stroke-linecap="round" opacity="0.85"/>
        <path d="M 60 110 Q 150 135, 240 105 T 400 120" fill="none" stroke="url(#collagenGrad)" stroke-width="3.5" stroke-linecap="round" opacity="0.75"/>

        <!-- Fibras Elásticas Ramificadas (Elasticidade) -->
        <path d="M 70 95 Q 120 120, 180 85 T 310 100 T 390 85" fill="none" stroke="var(--paletteAccent)" stroke-width="1.8" stroke-dasharray="6 3" opacity="0.9"/>

        <!-- Fibroblasto Ativo 1 (Célula Alongada que produz o colágeno) -->
        <g class="fibroblast fb1" transform="translate(130, 75)">
          <path d="M -45 0 Q -15 -18, 0 -12 Q 15 -18, 45 0 Q 15 18, 0 12 Q -15 18, -45 0 Z" fill="rgba(56, 189, 248, 0.25)" stroke="var(--palettePrimary)" stroke-width="2"/>
          <ellipse cx="0" cy="0" rx="10" ry="6" fill="var(--palettePrimary)" filter="url(#tissueGlow)"/>
          <text x="0" y="22" fill="#38bdf8" font-size="8.5" font-weight="800" text-anchor="middle">FIBROBLASTO</text>
        </g>

        <!-- Fibroblasto Ativo 2 -->
        <g class="fibroblast fb2" transform="translate(320, 110)">
          <path d="M -40 0 Q -12 -16, 0 -10 Q 12 -16, 40 0 Q 12 16, 0 10 Q -12 16, -40 0 Z" fill="rgba(168, 85, 247, 0.25)" stroke="var(--paletteAccent)" stroke-width="2"/>
          <ellipse cx="0" cy="0" rx="9" ry="5" fill="var(--paletteAccent)" filter="url(#tissueGlow)"/>
          <text x="0" y="22" fill="#c084fc" font-size="8.5" font-weight="800" text-anchor="middle">FIBROBLASTO</text>
        </g>

        <!-- Célula de Defesa Imunitária (Macrófago Fagocitário / Mastócito) -->
        <g class="macrophage" transform="translate(230, 48)">
          <circle cx="0" cy="0" r="16" fill="rgba(16, 185, 129, 0.2)" stroke="#10b981" stroke-width="2"/>
          <circle cx="-3" cy="-2" r="6" fill="#10b981"/>
          <text x="0" y="25" fill="#86efac" font-size="8" font-weight="800" text-anchor="middle">MACRÓFAGO</text>
        </g>

        <!-- Capilar Sanguíneo Nutritivo (Vascularização) -->
        <g transform="translate(230, 132)">
          <line x1="-150" y1="0" x2="150" y2="0" stroke="rgba(239, 68, 68, 0.4)" stroke-width="6" stroke-linecap="round"/>
          <circle cx="-60" cy="0" r="3.5" fill="#ef4444"/>
          <circle cx="0" cy="0" r="3.5" fill="#ef4444"/>
          <circle cx="60" cy="0" r="3.5" fill="#ef4444"/>
          <text x="0" y="12" fill="#fca5a5" font-size="7.5" font-weight="700" text-anchor="middle">CAPILAR SANGUÍNEO // NUTRIÇÃO</text>
        </g>
      </svg>
      <div class="bio-telemetry-badge" data-layout-ignore>
        <span class="bio-pulse-dot"></span> HISTOLOGIA // TECIDO CONJUNTIVO & MATRIZ EXTRACELULAR
      </div>
    </div>'''


# ==============================================================================
# RESOLUÇÃO PRECISA DO DOMÍNIO PEDAGÓGICO (ISOLAMENTO RÍGIDO DE DISCIPLINA)
# ==============================================================================

def resolve_topic_domain(topic: str, chapter_title: str = "") -> str:
    """Classifica com precisão matemática a macro-disciplina da aula para blindar contra contaminação entre matérias."""
    text = f" {topic} {chapter_title} ".lower()

    # 1. DIREITO & ADMINISTRAÇÃO PÚBLICA (CONCURSOS)
    if re.search(r"(\bdireito\b|constitucional|cf/88|cf\s*88|artigo\s*\d+|art\.\s*\d+|direitos\s+fundamentais|remédios\s+constitucionais|habeas\s+corpus|mandado\s+de\s+segurança|três\s+poderes|judiciário|legislativo|executivo|stf|stj|administrativo|limpe|legalidade|impessoalidade|moralidade|publicidade|eficiência|servidor\s+público|ato\s+administrativo|concurso\s+público|licitação|processo\s+disciplinar|órgão\s+público|oab)", text):
        return "LAW"

    # 2. GRAMÁTICA, LÍNGUA PORTUGUESA & REDAÇÃO
    if re.search(r"(\bcrase\b|acento\s+grave|regência|regencia|concordância|concordancia|preposição|preposicao|artigo\s+definido|artigo\s+indefinido|artigo\s+feminino|artigo\s+masculino|substantivo|adjetivo|pronome|verbo|análise\s+sintática|analise\s+sintatica|sujeito|predicado|oração|oracao|período\s+composto|pontuação|pontuacao|ortografia|acentuação|acentuacao|redação\s+enem|redacao\s+enem|nota\s+1000|língua\s+portuguesa|lingua\s+portuguesa|\bportuguês\b|\bportugues\b)", text):
        return "GRAMMAR"

    # 3. BIOLOGIA & SAÚDE
    if re.search(r"(\bbiologia\b|\bbiolog|célula|celular|tecido|histologia|histolog|conjuntiv|epitelial|ósseo|osseo|cartilag|muscular|sanguíneo|sanguineo|linfático|linfatico|adipos|fibroblasto|colágen|colagen|biogênese|biogenese|abiogênese|abiogenese|origem\s+da\s+vida|pasteur|redi|dna|genética|genetica|genoma|mitocôndria|mitocondria|mitose|meiose|organela|ecologia|trófic|trofic|cadeia\s+alimentar|fotossíntese|fotossintese|respiração\s+celular|respiracao\s+celular|neurônio|neuronio|sinapse|sistema\s+nervoso|imunologia|anticorpo|vacina|vírus|virus|bactéria|bacteria|\bevolução\b|\bevolucao\b|darwin|seleção\s+natural|anatomia|fisiologia)", text):
        return "BIOLOGY"

    # 4. FÍSICA
    if re.search(r"(\bfísica\b|\bfisica\b|newton|leis\s+de\s+newton|plano\s+inclinado|cinemática|cinematica|velocidade|aceleração|aceleracao|dinâmica|dinamica|gravitação|gravitacao|termodinâmica|termodinamica|óptica|optica|espelho|lente|ondulatória|ondulatoria|comprimento\s+de\s+onda|eletricidade|circuito|resistor|\bohm\b|voltagem|corrente\s+elétrica|corrente\s+eletrica|eletromagnetismo|indução|campo\s+magnético|mecânica\s+quântica|mecanica\s+quantica)", text):
        return "PHYSICS"

    # 5. QUÍMICA
    if re.search(r"(\bquímica\b|\bquimica\b|tabela\s+periódica|tabela\s+periodica|ligação\s+química|ligacao\s+quimica|ligação\s+covalente|ligação\s+iônica|estequiometria|\bmol\b|massa\s+molar|química\s+orgânica|quimica\s+organica|hidrocarboneto|benzeno|função\s+orgânica|isomeria|álcool|termoquímica|entalpia|cinética\s+química|\bph\b|ácido|base|titulação|soluções|eletroquímica|pilha|eletrólise)", text):
        return "CHEMISTRY"

    # 6. MATEMÁTICA & RACIOCÍNIO LÓGICO
    if re.search(r"(\bmatemática\b|\bmatematica\b|função\s+afim|função\s+quadrática|parábola|bhaskara|vértice|geometria|trigonometria|seno|cosseno|tangente|matriz|determinante|probabilidade|análise\s+combinatória|analise\s+combinatoria|estatística|estatistica|desvio\s+padrão|raciocínio\s+lógico|rlm|diagrama\s+de\s+venn|tabela[- ]verdade|lógica\s+proposicional)", text):
        return "MATH"

    # 7. HISTÓRIA
    if re.search(r"(\bhistória\b|\bhistoria\b|brasil\s+colônia|brasil\s+império|brasil\s+república|era\s+vargas|ditadura\s+militar|revolução|revolucao|século|seculo|idade\s+média|idade\s+moderna|feudalismo|iluminismo|primeira\s+guerra|segunda\s+guerra|guerra\s+fria)", text):
        return "HISTORY"

    # 8. GEOGRAFIA
    if re.search(r"(\bgeografia\b|placas\s+tectônicas|placas\s+tectonicas|tectônica|deriva\s+continental|relevo|orogênese|crosta|manto|vulcão|terremoto|clima|cartografia|bioma|demografia|urbanização|geopolítica)", text):
        return "GEOGRAPHY"

    # 9. FINANÇAS & MERCADO FINANCEIRO
    if re.search(r"(\bfinanças\b|\bfinancas\b|bolsa\s+de\s+valores|ibovespa|\bações\b|investimento|renda\s+fixa|selic|cdi|fundo\s+imobiliário|criptomoeda|bitcoin|balanço\s+patrimonial|valuation|dividendos)", text):
        return "FINANCE"

    # 10. PSICOLOGIA & COMPORTAMENTO
    if re.search(r"(\bpsicologia\b|psicanálise|psicanalise|freud|jung|saúde\s+mental|saude\s+mental|neurociência|neurociencia|viés\s+cognitivo|vies\s+cognitivo|behaviorismo)", text):
        return "PSYCHOLOGY"

    # 11. ASTRONOMIA & ASTROFÍSICA
    if re.search(r"(\bastronomia\b|astrofísica|astrofisica|quasar|buraco\s+negro|singularidade|horizonte\s+de\s+eventos|via\s+láctea|exoplaneta|telescópio\s+james\s+webb|cosmologia|supernova)", text):
        return "ASTRONOMY"

    return "GENERAL"


# ==============================================================================
# DETECTOR UNIVERSAL DE VESTIBULAR & CONCURSOS COM ISOLAMENTO DE DOMÍNIO
# ==============================================================================

def detect_vestibular_concurso_archetype(
    content: str,
    topic: str = "",
    chapter_title: str = "",
    sentence_index: int = 0,
) -> tuple[str, str]:
    """Classifica com rigor a sentença no arquétipo educacional exato, blindando contra mistura indevida de matérias."""
    c_lower = (content or "").lower()
    combined = f"{topic} {chapter_title} {content}".lower()
    domain = resolve_topic_domain(topic, chapter_title)

    # -------------------------------------------------------------------------
    # 1. ESCOPO: BIOLOGIA & SAÚDE (Totalmente isolado: Proibido Matemática/Direito/Finanças)
    # -------------------------------------------------------------------------
    if domain == "BIOLOGY":
        # Histologia / Tecido Conjuntivo e Matriz
        if re.search(r"(tecido\s+conjuntivo|colágen|colagen|matriz|fibroblasto|fibra|fibras|sustentação|sustentar|tendão|tendões|ligamento|cartilag|adipos|ósseo|absorver\s+choque|lesão|cicatriz|derme)", c_lower):
            return "bio_tissue", "HISTOLOGIA // TECIDO CONJUNTIVO & MATRIZ EXTRACELULAR"

        # Citologia / Fisiologia Celular
        if re.search(r"(célula|celular|membrana|mitose|meiose|organela|mitocôndria|proteína|proteina|citoplasma|núcleo)", c_lower):
            return "biogenesis_cell", "BIOLOGIA // ESTRUTURA CELULAR"

        # Fisiologia / Sistema Nervoso
        if re.search(r"(neurônio|neuronio|sinapse|sistema nervoso|cérebro|potencial de ação|neurotransmissor)", c_lower):
            return "bio_neuron", "FISIOLOGIA // SISTEMA NERVOSO & SINAPSE"

        # Ecologia e Níveis Tróficos
        if re.search(r"(ecologia|cadeia alimentar|teia trófica|pirâmide de energia|produtores|consumidores|bioma)", c_lower):
            return "bio_ecology", "ECOLOGIA // PIRÂMIDE TRÓFICA"

        # Genética e DNA
        if re.search(r"(dna|genética|genetica|gene|genes|código genético|dupla hélice|replicação)", c_lower):
            return "biogenesis_dna", "GENÉTICA // DUPLA HÉLICE & CÓDIGO CELULAR"

        # Experimentos Clássicos de Origem da Vida
        if re.search(r"(pasteur|pescoço de cisne|caldo fervido|esterilização)", c_lower):
            return "biogenesis_pasteur", "EXPERIMENTO DE PASTEUR // ORIGEM DA VIDA"
        if re.search(r"(redi|francesco|mosca|moscas|larva|larvas|pote|potes|carne)", c_lower):
            return "biogenesis_redi", "EXPERIMENTO DE REDI // BIOGÊNESE"
        if re.search(r"(abiogênese|abiogenese|geração espontânea|mito|inanimada|versus|vs)", c_lower):
            return "biogenesis_versus", "ABIOGÊNESE vs BIOGÊNESE"

        # Microscopia / Infecções / Defesa
        if re.search(r"(microscóp|microscop|bactéria|bacteria|vírus|virus|micróbio|infecção|infeccao|combater|anticorpo|imun)", c_lower):
            return "biogenesis_microscope", "MICROSCOPIA // DEFESA & CÉLULAS"

        # Fallback rotacional estritamente biológico para garantir dinamismo visual sem sair da biologia
        bio_cycle = [
            ("bio_tissue", "HISTOLOGIA // TECIDO CONJUNTIVO & MATRIZ"),
            ("biogenesis_cell", "BIOLOGIA // CITOLOGIA & CÉLULAS"),
            ("biogenesis_microscope", "MICROSCOPIA // ULTRAESTRUTURA"),
            ("bio_tissue", "HISTOLOGIA // FIBRAS DE COLÁGENO"),
            ("biogenesis_dna", "GENÉTICA // CÓDIGO BIOLÓGICO"),
            ("bio_neuron", "FISIOLOGIA // COORDENAÇÃO TECIDUAL"),
        ]
        return bio_cycle[sentence_index % len(bio_cycle)]

    # -------------------------------------------------------------------------
    # 2. ESCOPO: DIREITO & CONCURSOS PÚBLICOS
    # -------------------------------------------------------------------------
    if domain == "LAW":
        if re.search(r"(constituição|constituicao|cf/88|artigo 5|direitos fundamentais|remédios constitucionais|habeas corpus|mandado de segurança|três poderes|judiciário|legislativo|executivo|stf)", c_lower):
            return "law_constitution", "DIREITO CONSTITUCIONAL // CF/88"
        if re.search(r"(administrativo|limpe|legalidade|impessoalidade|moralidade|publicidade|eficiência|servidor público|ato administrativo|concurso público|licitação|processo disciplinar|órgão público)", c_lower):
            return "law_limpe", "DIREITO ADMINISTRATIVO // L.I.M.P.E."
        if re.search(r"(tabela-verdade|proposição|lógica proposicional|conectivo|se\.\.\. então)", c_lower):
            return "logic_truth_table", "RACIOCÍNIO LÓGICO // PROPOSIÇÕES"
        if re.search(r"(sintaxe|concordância|regência|redação oficial)", c_lower):
            return "grammar_syntax", "NORMA CULTA // REDAÇÃO DE CONCURSO"

        law_cycle = [
            ("law_constitution", "DIREITO CONSTITUCIONAL // CF/88"),
            ("law_limpe", "DIREITO ADMINISTRATIVO // PRINCÍPIOS"),
            ("logic_truth_table", "RACIOCÍNIO LÓGICO // PROPOSIÇÕES"),
            ("grammar_syntax", "NORMA CULTA // REDAÇÃO OFICIAL"),
        ]
        return law_cycle[sentence_index % len(law_cycle)]

    # -------------------------------------------------------------------------
    # 3. ESCOPO: GRAMÁTICA, LÍNGUA PORTUGUESA & REDAÇÃO
    # -------------------------------------------------------------------------
    if domain == "GRAMMAR":
        if re.search(r"(sujeito|predicado|objeto direto|objeto indireto|oração|período composto|transitivo|conjunção)", c_lower):
            return "grammar_syntax", "NORMA CULTA // ANÁLISE SINTÁTICA"
        if re.search(r"(redação\s+enem|nota 1000|proposta de intervenção|competência|dissertativo)", c_lower):
            return "redacao_enem", "REDAÇÃO NOTA 1000 // COMPETÊNCIAS ENEM"

        grammar_cycle = [
            ("grammar", "NORMA PADRÃO // REGÊNCIA & CRASE"),
            ("grammar_syntax", "NORMA CULTA // ANÁLISE SINTÁTICA"),
            ("comparison", "CERTO vs ERRADO // APLICAÇÃO"),
            ("lesson", "DICA DE OURO // MACETE PRÁTICO"),
        ]
        return grammar_cycle[sentence_index % len(grammar_cycle)]

    # -------------------------------------------------------------------------
    # 4. ESCOPO: FÍSICA
    # -------------------------------------------------------------------------
    if domain == "PHYSICS":
        if re.search(r"(newton|plano inclinado|força peso|força normal|atrito|cinemática|cinematica|velocidade|aceleração|gravidade|dinâmica)", c_lower):
            return "physics_mechanics", "FÍSICA MECÂNICA // LEIS DE NEWTON"
        if re.search(r"(circuito|resistor|ohm|voltagem|corrente elétrica|ampere|ddp|potência elétrica)", c_lower):
            return "physics_circuits", "ELETRODINÂMICA // LEIS DE OHM"
        if re.search(r"(gráfico|curva|parábola|cartesiano|trajetória)", c_lower):
            return "math_cartesian", "CINEMÁTICA // GRÁFICOS DO MOVIMENTO"

        phys_cycle = [
            ("physics_mechanics", "FÍSICA // DINÂMICA & NEWTON"),
            ("physics_circuits", "ELETRODINÂMICA // CIRCUITO & OHM"),
            ("formula", "EQUAÇÕES FUNDAMENTAIS DA FÍSICA"),
        ]
        return phys_cycle[sentence_index % len(phys_cycle)]

    # -------------------------------------------------------------------------
    # 5. ESCOPO: QUÍMICA
    # -------------------------------------------------------------------------
    if domain == "CHEMISTRY":
        if re.search(r"(orgânica|benzeno|anel aromático|carbono|hidrocarboneto|isomeria|álcool|aldeído|fenol)", c_lower):
            return "chemistry_organic", "QUÍMICA ORGÂNICA // CADEIAS CARBÔNICAS"
        if re.search(r"(ph|ácido|base|alcalino|termoquímica|reação química|entalpia|cinética|catalisador)", c_lower):
            return "chemistry_reaction", "FÍSICO-QUÍMICA // pH & REAÇÕES"

        chem_cycle = [
            ("chemistry_organic", "QUÍMICA ORGÂNICA // CADEIAS"),
            ("chemistry_reaction", "FÍSICO-QUÍMICA // pH & CINÉTICA"),
            ("quantum", "ESTRUTURA ATÔMICA & LIGAÇÕES"),
        ]
        return chem_cycle[sentence_index % len(chem_cycle)]

    # -------------------------------------------------------------------------
    # 6. ESCOPO: MATEMÁTICA & RLM
    # -------------------------------------------------------------------------
    if domain == "MATH":
        if re.search(r"(\bfunção\b|\bfuncao\b|parábola|vértice|raízes|plano cartesiano|eixo x|eixo y|afim|quadrática|bhaskara)", c_lower):
            return "math_cartesian", "MATEMÁTICA // FUNÇÕES & GRÁFICOS"
        if re.search(r"(diagrama de venn|conjuntos|intersecção|união|pertence)", c_lower):
            return "logic_venn", "RACIOCÍNIO LÓGICO // DIAGRAMA DE VENN"
        if re.search(r"(tabela-verdade|proposição|se\.\.\. então|tautologia|conjunção|disjunção)", c_lower):
            return "logic_truth_table", "LÓGICA PROPOSICIONAL // TABELA-VERDADE"

        math_cycle = [
            ("math_cartesian", "MATEMÁTICA // FUNÇÕES & GRÁFICOS"),
            ("logic_venn", "RACIOCÍNIO LÓGICO // CONJUNTOS"),
            ("logic_truth_table", "LÓGICA PROPOSICIONAL // VALORAÇÃO"),
            ("analytics", "ESTATÍSTICA // DADOS & TENDÊNCIA"),
        ]
        return math_cycle[sentence_index % len(math_cycle)]

    # -------------------------------------------------------------------------
    # 7. ESCOPO: HISTÓRIA
    # -------------------------------------------------------------------------
    if domain == "HISTORY":
        return "history_brazil", "HISTÓRIA // CRONOLOGIA & MARCOS"

    # -------------------------------------------------------------------------
    # 8. ESCOPO: GEOGRAFIA
    # -------------------------------------------------------------------------
    if domain == "GEOGRAPHY":
        return "geo_plates", "GEOGRAFIA // TECTÔNICA & RELEVO"

    # -------------------------------------------------------------------------
    # 9. DOMÍNIO GERAL OU NÃO ESPECIFICADO (Exige contexto específico para evitar falso-positivo)
    # -------------------------------------------------------------------------
    if re.search(r"(constituição|cf/88|artigo 5|direitos fundamentais|remédios constitucionais)", c_lower):
        return "law_constitution", "DIREITO CONSTITUCIONAL // CF/88"
    if re.search(r"(administrativo|limpe|legalidade|servidor público|ato administrativo)", c_lower):
        return "law_limpe", "DIREITO ADMINISTRATIVO // L.I.M.P.E."
    if re.search(r"(diagrama de venn|intersecção de conjuntos)", c_lower):
        return "logic_venn", "RACIOCÍNIO LÓGICO // DIAGRAMA DE VENN"
    if re.search(r"(tabela-verdade|proposição lógica|se\.\.\. então)", c_lower):
        return "logic_truth_table", "LÓGICA PROPOSICIONAL // TABELA-VERDADE"
    if re.search(r"(sujeito e predicado|objeto direto|oração subordinada)", c_lower):
        return "grammar_syntax", "NORMA CULTA // ANÁLISE SINTÁTICA"
    if re.search(r"(redação nota 1000|proposta de intervenção enem)", c_lower):
        return "redacao_enem", "REDAÇÃO NOTA 1000 // COMPETÊNCIAS ENEM"
    if re.search(r"(função afim|função quadrática|parábola da função|plano cartesiano|vértice da parábola)", c_lower):
        return "math_cartesian", "MATEMÁTICA // FUNÇÕES & GRÁFICOS"
    if re.search(r"(leis de newton|plano inclinado|força peso e normal)", c_lower):
        return "physics_mechanics", "FÍSICA MECÂNICA // LEIS DE NEWTON"
    if re.search(r"(circuito elétrico|lei de ohm|resistor em série)", c_lower):
        return "physics_circuits", "ELETRODINÂMICA // LEIS DE OHM"
    if re.search(r"(química orgânica|anel aromático|anel benzênico)", c_lower):
        return "chemistry_organic", "QUÍMICA ORGÂNICA // CADEIAS CARBÔNICAS"
    if re.search(r"(escala de ph|reação endotérmica|entalpia de reação)", c_lower):
        return "chemistry_reaction", "FÍSICO-QUÍMICA // pH & REAÇÕES"
    if re.search(r"(pirâmide trófica|níveis tróficos|cadeia alimentar)", c_lower):
        return "bio_ecology", "ECOLOGIA // PIRÂMIDE TRÓFICA"
    if re.search(r"(neurônio e sinapse|potencial de ação nervosa)", c_lower):
        return "bio_neuron", "FISIOLOGIA // SISTEMA NERVOSO & SINAPSE"
    if re.search(r"(placas tectônicas|tectônica de placas|deriva continental)", c_lower):
        return "geo_plates", "GEOGRAFIA // TECTÔNICA & RELEVO"

    return "", ""



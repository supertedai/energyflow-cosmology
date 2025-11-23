"""
SYMBIOSE MATH ENGINE
====================
Gir deg:
- Math Enforcer (pre-filter)
- Math Sanitizer (unicode→LaTeX + wrapping)
- Math Validator (syntaksfeil i LaTeX)
- Math Beautifier (nummerering, spacing)
- EFC Math Mode (spesialoperatorer fra din kosmologi)
"""

import re

# -----------------------------------------------------------
# 1. PRE-FILTER → Tving modellen inn i ren LaTeX
# -----------------------------------------------------------

def math_enforcer(prompt: str) -> str:
    rules = (
        "Du er i Matematikk-Modus. All matematikk skal skrives i ren LaTeX. "
        "Bruk kun \\( ... \\) for inline og \\[ ... \\] for display. "
        "Ingen unicode, ingen tekstblanding inni formler, ingen markdown-kodeblokker. "
        "Reparer alltid uttrykk slik at resultatet er gyldig LaTeX. "
        "Bruk EFC-operatørene definert nedenfor når relevant."
        "\n\n"
        + EFC_MATH_MODE
        + "\n\n"
        "Start nå."
    )
    return rules + "\n" + prompt


# -----------------------------------------------------------
# 2. SANITIZER → unicode → LaTeX + wrapping av 'løse' formler
# -----------------------------------------------------------

UNICODE_MAP = {
    "×": r"\times ",
    "·": r"\cdot ",
    "∂": r"\partial ",
    "∇": r"\nabla ",
    "∞": r"\infty ",
    "±": r"\pm ",
    "≤": r"\leq ",
    "≥": r"\geq ",
    "≠": r"\neq ",
    "√": r"\sqrt{}",
    "λ": r"\lambda",
    "Σ": r"\Sigma",
    "Δ": r"\Delta",
}

def sanitize_unicode(text: str) -> str:
    for k, v in UNICODE_MAP.items():
        text = text.replace(k, v)
    return text

def wrap_loose_math(text: str) -> str:
    pattern = r"([A-Za-z0-9\^_\/\*\+\-\(\) ]+=+[A-Za-z0-9\^_\/\*\+\-\(\) ]+)"
    return re.sub(pattern, lambda m: r"\[ " + m.group(1) + r" \]", text)

def math_sanitizer(text: str) -> str:
    text = sanitize_unicode(text)
    text = wrap_loose_math(text)
    return text


# -----------------------------------------------------------
# 3. VALIDATOR → Oppdager åpenbare LaTeX-syntaksfeil
# -----------------------------------------------------------

def math_validator(text: str) -> str:
    issues = []

    # Enkle feil: ubalanserte {} eller \[ \]
    if text.count("{") != text.count("}"):
        issues.append("Ubalanserte klammeparenteser {}.")

    if text.count("\\[") != text.count("\\]"):
        issues.append("Ubalanserte display-formler \\[ \\].")

    if issues:
        return text + "\n\n% VALIDATOR ADVARSEL:\n% " + " ".join(issues)

    return text


# -----------------------------------------------------------
# 4. BEAUTIFIER → nummerering av formler + spacing
# -----------------------------------------------------------

def beautify_equations(text: str) -> str:
    lines = text.split("\n")
    count = 1
    out = []

    for line in lines:
        if line.strip().startswith("\\[") and line.strip().endswith("\\]"):
            numbered = (
                f"\\begin{{equation}}\n"
                f"{line.strip()[2:-2].strip()}\n"
                f"\\label{{eq:{count}}}\n"
                f"\\end{{equation}}\n"
            )
            out.append(numbered)
            count += 1
        else:
            out.append(line)

    return "\n".join(out)


# -----------------------------------------------------------
# 5. EFC-MATH-MODE → Dine spesialoperatorer
# -----------------------------------------------------------

EFC_MATH_MODE = r"""
% --------------------------
%   EFC Math Mode Operators
% --------------------------

\newcommand{\GridGrad}{\nabla_{\text{grid}}}
\newcommand{\EntropyFlow}{\Phi_{\text{entropy}}}
\newcommand{\Flow}{\mathcal{F}}
\newcommand{\sZero}{s_{0}}
\newcommand{\sOne}{s_{1}}
\newcommand{\HaloT}{T_{\text{halo}}}
\newcommand{\CMBT}{T_{\text{CMB}}}
\newcommand{\LightSpeed}{c}
\newcommand{\EnergyDensity}{\rho_E}
\newcommand{\EntropyGrad}{\nabla S}
"""


# -----------------------------------------------------------
# 6. MASTER FILTER PIPELINE
# -----------------------------------------------------------

def process_math(text: str) -> str:
    stage1 = sanitize_unicode(text)
    stage2 = wrap_loose_math(stage1)
    stage3 = math_validator(stage2)
    stage4 = beautify_equations(stage3)
    return stage4

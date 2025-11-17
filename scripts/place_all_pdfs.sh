#!/usr/bin/env bash
set -e

SRC="restored_pdfs"

# Ensure folders
mkdir -p theory/formal
mkdir -p docs/archive
mkdir -p docs/articles
mkdir -p docs/cognition
mkdir -p methodology

move() {
  file="$1"
  target="$2"
  if [ -f "$SRC/$file" ]; then
    mv "$SRC/$file" "$target/$file"
    echo "Moved $file → $target/"
  fi
}

# Formal PDFs
move efc_formal_spec.pdf theory/formal
move efc_master.pdf theory/formal
move efc_master_v1.pdf theory/formal
move EFC-Mathematical-Framework-for-Energy-Flow-in-Space-Time.pdf theory/formal
move EFC-Technical-Documentation-Energy-Flow-in-Space-Time.pdf theory/formal
move EFC-Field-Equations-for-Entropy-Driven-Spacetime.pdf theory/formal
move EFC-Thermodynamic-Bridge-GR-QFT.pdf theory/formal

# Archive PDFs
move EFC-v1.2-Foundational-Framework.pdf docs/archive
move EFC-v2.1-Modular-Synthesis.pdf docs/archive
move EFC-v2.1-Complete-Edition.pdf docs/archive
move EFC-v2.2-Cross-Field-Integration-Summary.pdf docs/archive

# Cognition
move CEM-Consciousness-Ego-Mirror.pdf docs/cognition

# Methodology
move ai_workflow_framework.pdf methodology
move EFC-AI-Augmented-Scientific-Workflow-Framework.pdf methodology

# Everything else → articles
for f in $SRC/EFC-*.pdf; do
  [ -e "$f" ] || continue
  base=$(basename "$f")

  case "$base" in
    EFC-Mathematical-Framework-for-Energy-Flow-in-Space-Time.pdf|\
    EFC-Technical-Documentation-Energy-Flow-in-Space-Time.pdf|\
    EFC-Field-Equations-for-Entropy-Driven-Spacetime.pdf|\
    EFC-Thermodynamic-Bridge-GR-QFT.pdf|\
    EFC-v1.2-Foundational-Framework.pdf|\
    EFC-v2.1-Modular-Synthesis.pdf|\
    EFC-v2.1-Complete-Edition.pdf|\
    EFC-v2.2-Cross-Field-Integration-Summary.pdf|\
    EFC-AI-Augmented-Scientific-Workflow-Framework.pdf)
      continue
      ;;
  esac

  mv "$f" docs/articles/"$base"
  echo "Moved $base → docs/articles/"
done

echo "✔ All PDFs placed correctly."

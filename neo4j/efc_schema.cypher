// ===============================================
// EFC GRAPH SCHEMA — CORE
// Kjør denne én gang i Aura
// ===============================================

// ---------- Concept ----------
CREATE CONSTRAINT IF NOT EXISTS
FOR (c:Concept)
REQUIRE c.slug IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS
FOR (c:Concept)
REQUIRE c.id IS UNIQUE;

// ---------- Paper ----------
CREATE CONSTRAINT IF NOT EXISTS
FOR (p:Paper)
REQUIRE p.doi IS UNIQUE;

CREATE CONSTRAINT IF NOT EXISTS
FOR (p:Paper)
REQUIRE p.id IS UNIQUE;

// ---------- Figure ----------
CREATE CONSTRAINT IF NOT EXISTS
FOR (f:Figure)
REQUIRE f.id IS UNIQUE;

// ---------- Dataset ----------
CREATE CONSTRAINT IF NOT EXISTS
FOR (d:Dataset)
REQUIRE d.id IS UNIQUE;

// ---------- Tag (valgfritt, men nyttig) ----------
CREATE CONSTRAINT IF NOT EXISTS
FOR (t:Tag)
REQUIRE t.name IS UNIQUE;

// ===============================================
// STANDARD PROPS (anbefalt, ikke tvang)
// ===============================================
// Concept:
//  - id: string (stable, internal)
//  - slug: string (human/URL key, e.g. "grid-higgs-framework")
//  - name: string
//  - summary: short text
//  - category: "core" | "structure" | "dynamics" | "cognition" | "methodology" | ...
//  - level: integer (0..3, f.eks. 0=core, 1=derived, 2=applied, 3=meta)
//  - status: "draft" | "active" | "archived"
//  - created_at, updated_at: ISO timestamp

// Paper:
//  - id: string (internal, f.eks. "AUTH-Layer-2025-v1.0")
//  - title: string
//  - doi: string
//  - version: string
//  - year: integer
//  - figshare_id: string
//  - path: relative path i GitHub
//  - url: public URL (GitHub/Figshare)

// Figure:
//  - id: string (f.eks. "AUTH-Fig-1")
//  - label: "Figure 1"
//  - caption: kort tekst
//  - path: filsti i repoet

// Dataset:
//  - id: string (f.eks. "SPARC-RC")
//  - name: string
//  - source: "SPARC", "JWST", "DESI", ...
//  - doi: string
//  - url: dataset-URL

// ===============================================
// RELATIONSHIP-TYPER
// ===============================================
//
//  (Paper)-[:DESCRIBES]->(Concept)
//  (Concept)-[:REFINES]->(Concept)
//  (Concept)-[:DEPENDS_ON]->(Concept)
//  (Concept)-[:RELATES_TO]->(Concept)
//  (Concept)-[:ILLUSTRATED_BY]->(Figure)
//  (Concept)-[:VALIDATED_BY]->(Dataset)
//  (Paper)-[:HAS_FIGURE]->(Figure)
//  (Paper)-[:USES_DATASET]->(Dataset)
//  (Concept)-[:TAGGED_WITH]->(Tag)
// ===============================================

# 🔧 EFC Workflow Map  
Automated CI/CD + Semantic Synchronization Pipeline

This document describes how the EFC repository updates itself.  
It shows how data flows, how automation works, and how semantic nodes stay consistent across Figshare, GitHub Actions, the API, and the dashboard.

---

## 📡 1. Overview

The system maintains and updates:

- **Semantics** (`schema/*`)
- **Metadata** (Figshare → GitHub)
- **Validation** (JWST, DESI, SPARC)
- **API snapshots** (`api/v1/`)
- **Dashboard** (`docs/dashboard/` or similar)
- **Documentation** (README + project files)
- **Reflection** (`reflection/`)

Each workflow is a module.  
Together they form a continuous semantic loop.

---

## 🧩 2. Workflow Dependency Graph

```mermaid
flowchart TD

%% === Fetch Layer ===
F1[fetch-figshare.yml<br>Fetch DOI metadata]

%% === Schema Merge Layer ===
SC1[update-concepts.yml<br>Update schema/]
F1 --> SC1

%% === API Generation Layer ===
API1[update-api.yml<br>Regenerate api/v1/]
SC1 --> API1

%% === Dashboard Layer ===
DB1[build-dashboard.yml<br>Update dashboard]
API1 --> DB1

%% === Output Layer ===
VAL[run-validation.yml<br>JWST / DESI / SPARC]
VAL --> OUT[output/<br>plots + metrics]

%% === Export Layer ===
OUT --> FS[export_figshare.yml<br>Upload to Figshare]

%% === Master Orchestrator ===
META[update_efc_system.yml<br>Daily full cycle]
META --> F1
META --> SC1
META --> API1
META --> DB1
⚙️ 3. Workflow Functions
Workflow	Purpose	Trigger
fetch-figshare.yml	Fetch DOI metadata → /figshare/	Manual / API / Meta
update-concepts.yml	Update concepts.json and site-graph.json	After Figshare fetch
update-api.yml	Regenerate api/v1/ JSON-LD endpoints	On schema changes
build-dashboard.yml	Rebuild dashboard views	On API or data updates
run-validation.yml	JWST / DESI / SPARC validation	On every push to main
export_figshare.yml	Upload new plots/data to Figshare	When /output/ changes
update-readme-date.yml	Refresh timestamp in README	Daily
update-schema.yml	Validate schema + regenerate schema maps	On /schema/ changes
update_efc_system.yml	Full orchestrated sync cycle	Daily 02:00 UTC

🔄 4. The EFC Semantic Loop
The core loop:

1. Fetch

Pull the latest DOI metadata from Figshare.

Update JSON files under /figshare/.

2. Merge

Integrate metadata into:

/schema/concepts.json

/schema/site-graph.json

3. API Regeneration

Regenerate /api/v1/:

terms.json index.

One JSON-LD document per concept.

Used by:

Website.

Dashboard.

LLMs.

External crawlers and tools.

4. Dashboard Update

Read API and validation outputs.

Build fresh visual summaries and status views.

5. Reflection Layer

Write system status into /reflection/.

Track semantic coherence, resonance, and cross-links.

The loop stops if validation or import tests fail.

📊 5. Validation Pipeline
The validation line covers three dataset families:

JWST early galaxies.

DESI expansion curve.

SPARC rotation curves.

For each dataset:

Import src/efc/* modules.

Run EFC calculations.

Produce figures and metrics under output/validation/.

Run scripts/check_imports.py to confirm clean imports.

If any step fails, the workflow fails and blocks further stages.

🧪 6. Import Test Suite
scripts/check_imports.py ensures:

All src/efc/* submodules import without errors.

No circular imports appear.

Refactors keep the public API stable.

Validation and API generation see the same core code.

It acts as a safety gate before validation and API steps.

🌐 7. External Integration Map
Four external anchors:

GitHub → code, workflows, API snapshots.

Figshare → DOIs, archived outputs.

ORCID → authorship and provenance.

energyflow-cosmology.com → public presentation and dashboard.

Typical flow:

Code and schema live in GitHub.

Outputs and figures sync to Figshare with DOIs.

Website pulls structured data from:

/schema/

/api/v1/

Figshare endpoints.

ORCID connects the work to the author identity.

🧠 8. Purpose of the Workflow Layer
The workflow layer provides:

Reproducible open science.

Up-to-date metadata and concepts.

Automatic testing of cosmology predictions.

Stable machine-readable API for search and AI systems.

Transparent provenance through ORCID + DOI.

A consistent semantic structure across platforms.

The system behaves like a thermodynamic knowledge graph:
it updates, stabilizes, and corrects itself over time.

🏗️ 9. Architecture Diagram (Theory → Code → Data → Semantics)
mermaid
Kopier kode
flowchart TD

%% === Theory Layer ===
T1[theory/<br>EFC-S / EFC-D / EFC-C / IMX] 
T2[theory/architecture.md<br>Model architecture]

T1 --> T2

%% === Source Code Layer ===
subgraph SRC[ src/efc/ ]
    C1[efc_core.py<br>core model]
    C2[efc_potential.py<br>energy-flow potential]
    C3[efc_entropy.py<br>entropy field + gradient]
    C4[efc_validation.py<br>astro validation tools]
end

T2 --> SRC

%% === Scripts ===
subgraph SCRIPTS[ scripts/ ]
    S1[run_efc_baseline.py<br>baseline runs]
    S2[validate_efc.py<br>JWST / DESI / SPARC]
    S3[check_imports.py<br>import test gate]
    S4[update_efc_api.py<br>generate api/v1/]
end

SRC --> S1
SRC --> S2
SRC --> S3
SRC --> S4

%% === Data ===
subgraph DATA[data/ + external]
    D1[JWST catalogs]
    D2[DESI / BAO data]
    D3[SPARC rotation curves]
end

D1 --> S2
D2 --> S2
D3 --> S2

S2 --> OUT1[output/validation/<br>figures + metrics]
S1 --> OUT2[output/baseline/]

%% === Semantics ===
subgraph SEM[Semantic Layer]
    SC1[schema/concepts.json<br>concept graph]
    SC2[schema/site-graph.json<br>Auth node and site map]
    SC3[figshare-index.json<br>DOI links]
    SC4[methodology/<br>Open method & symbiosis]
end

SC1 --> S4
S4 --> API[api/v1/<br>JSON-LD endpoints]

%% === Open Science ===
OUT1 --> FS[Export to Figshare]
OUT2 --> FS
SC1 --> FS
SC3 --> FS

FS --> DOI[Figshare DOIs]

%% === Reflection Layer ===
API --> REF[reflection/<br>symbiosis + meta-analysis]
T1 --> REF
SC2 --> REF
FS --> REF
📅 Last Updated
Automatically updated by update-readme-date.yml.

php-template
Kopier kode

---

### `project/WORKFLOW_MAP.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>EFC Workflow Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { max-width: 900px; margin: 2rem auto; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.5; }
    h1, h2, h3 { margin-top: 1.6rem; }
    code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
    pre { background: #f5f5f5; padding: 1rem; overflow-x: auto; border-radius: 6px; }
    table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
    th, td { border: 1px solid #ccc; padding: 0.5rem; text-align: left; }
    th { background: #f0f0f0; }
    ul { margin-left: 1.2rem; }
  </style>
</head>
<body>

<h1>🔧 EFC Workflow Map</h1>
<p>Automated CI/CD + Semantic Synchronization Pipeline</p>

<p>
This document describes how the EFC repository updates itself.
It shows how data flows, how automation works, and how semantic nodes stay consistent across Figshare, GitHub Actions, the API, and the dashboard.
</p>

<h2>📡 1. Overview</h2>
<p>The system maintains and updates:</p>
<ul>
  <li><strong>Semantics</strong> (<code>schema/*</code>)</li>
  <li><strong>Metadata</strong> (Figshare → GitHub)</li>
  <li><strong>Validation</strong> (JWST, DESI, SPARC)</li>
  <li><strong>API snapshots</strong> (<code>api/v1/</code>)</li>
  <li><strong>Dashboard</strong> (<code>docs/dashboard/</code> or similar)</li>
  <li><strong>Documentation</strong> (README + project files)</li>
  <li><strong>Reflection</strong> (<code>reflection/</code>)</li>
</ul>
<p>Each workflow is a module. Together they form a continuous semantic loop.</p>

<h2>🧩 2. Workflow Dependency Graph</h2>
<pre><code class="language-mermaid">
flowchart TD

%% === Fetch Layer ===
F1[fetch-figshare.yml&lt;br&gt;Fetch DOI metadata]

%% === Schema Merge Layer ===
SC1[update-concepts.yml&lt;br&gt;Update schema/]
F1 --&gt; SC1

%% === API Generation Layer ===
API1[update-api.yml&lt;br&gt;Regenerate api/v1/]
SC1 --&gt; API1

%% === Dashboard Layer ===
DB1[build-dashboard.yml&lt;br&gt;Update dashboard]
API1 --&gt; DB1

%% === Output Layer ===
VAL[run-validation.yml&lt;br&gt;JWST / DESI / SPARC]
VAL --&gt; OUT[output/&lt;br&gt;plots + metrics]

%% === Export Layer ===
OUT --&gt; FS[export_figshare.yml&lt;br&gt;Upload to Figshare]

%% === Master Orchestrator ===
META[update_efc_system.yml&lt;br&gt;Daily full cycle]
META --&gt; F1
META --&gt; SC1
META --&gt; API1
META --&gt; DB1
</code></pre>

<h2>⚙️ 3. Workflow Functions</h2>
<table>
  <thead>
    <tr>
      <th>Workflow</th>
      <th>Purpose</th>
      <th>Trigger</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>fetch-figshare.yml</strong></td>
      <td>Fetch DOI metadata → <code>/figshare/</code></td>
      <td>Manual / API / Meta</td>
    </tr>
    <tr>
      <td><strong>update-concepts.yml</strong></td>
      <td>Update <code>concepts.json</code> and <code>site-graph.json</code></td>
      <td>After Figshare fetch</td>
    </tr>
    <tr>
      <td><strong>update-api.yml</strong></td>
      <td>Regenerate <code>api/v1/</code> JSON-LD endpoints</td>
      <td>On schema changes</td>
    </tr>
    <tr>
      <td><strong>build-dashboard.yml</strong></td>
      <td>Rebuild dashboard views</td>
      <td>On API or data updates</td>
    </tr>
    <tr>
      <td><strong>run-validation.yml</strong></td>
      <td>JWST / DESI / SPARC validation</td>
      <td>On every push to <code>main</code></td>
    </tr>
    <tr>
      <td><strong>export_figshare.yml</strong></td>
      <td>Upload new plots/data to Figshare</td>
      <td>When <code>/output/</code> changes</td>
    </tr>
    <tr>
      <td><strong>update-readme-date.yml</strong></td>
      <td>Refresh timestamp in README</td>
      <td>Daily</td>
    </tr>
    <tr>
      <td><strong>update-schema.yml</strong></td>
      <td>Validate schema + regenerate schema maps</td>
      <td>On <code>/schema/</code> changes</td>
    </tr>
    <tr>
      <td><strong>update_efc_system.yml</strong></td>
      <td>Full orchestrated sync cycle</td>
      <td>Daily 02:00 UTC</td>
    </tr>
  </tbody>
</table>

<h2>🔄 4. The EFC Semantic Loop</h2>
<p>The core loop:</p>
<h3>1. Fetch</h3>
<ul>
  <li>Pull the latest DOI metadata from Figshare.</li>
  <li>Update JSON files under <code>/figshare/</code>.</li>
</ul>

<h3>2. Merge</h3>
<ul>
  <li>Integrate metadata into <code>/schema/concepts.json</code> and <code>/schema/site-graph.json</code>.</li>
</ul>

<h3>3. API Regeneration</h3>
<ul>
  <li>Regenerate <code>/api/v1/</code> (index + one JSON-LD per concept).</li>
  <li>Serve website, dashboard, LLMs and external tools.</li>
</ul>

<h3>4. Dashboard Update</h3>
<ul>
  <li>Read API and validation outputs.</li>
  <li>Build updated visual summaries and status views.</li>
</ul>

<h3>5. Reflection Layer</h3>
<ul>
  <li>Write system status into <code>/reflection/</code>.</li>
  <li>Track semantic coherence, resonance, and cross-links.</li>
</ul>

<p>The loop stops if validation or import tests fail.</p>

<h2>📊 5. Validation Pipeline</h2>
<p>The validation line covers three dataset families:</p>
<ul>
  <li>JWST early galaxies.</li>
  <li>DESI expansion curve.</li>
  <li>SPARC rotation curves.</li>
</ul>
<p>For each dataset:</p>
<ul>
  <li>Import <code>src/efc/*</code> modules.</li>
  <li>Run EFC calculations.</li>
  <li>Produce figures and metrics under <code>output/validation/</code>.</li>
  <li>Run <code>scripts/check_imports.py</code> to confirm clean imports.</li>
</ul>

<h2>🧪 6. Import Test Suite</h2>
<p><code>scripts/check_imports.py</code> ensures:</p>
<ul>
  <li>All <code>src/efc/*</code> submodules import without errors.</li>
  <li>No circular imports appear.</li>
  <li>Refactors keep the public API stable.</li>
  <li>Validation and API generation see the same core code.</li>
</ul>

<h2>🌐 7. External Integration Map</h2>
<p>Four external anchors:</p>
<ul>
  <li><strong>GitHub</strong> → code, workflows, API snapshots.</li>
  <li><strong>Figshare</strong> → DOIs, archived outputs.</li>
  <li><strong>ORCID</strong> → authorship and provenance.</li>
  <li><strong>energyflow-cosmology.com</strong> → public presentation and dashboard.</li>
</ul>

<h2>🧠 8. Purpose of the Workflow Layer</h2>
<ul>
  <li>Reproducible open science.</li>
  <li>Up-to-date metadata and concepts.</li>
  <li>Automatic testing of cosmology predictions.</li>
  <li>Stable machine-readable API for search and AI systems.</li>
  <li>Transparent provenance through ORCID + DOI.</li>
  <li>Consistent semantic structure across platforms.</li>
</ul>

<h2>🏗️ 9. Architecture Diagram</h2>
<pre><code class="language-mermaid">
flowchart TD

%% === Theory Layer ===
T1[theory/&lt;br&gt;EFC-S / EFC-D / EFC-C / IMX] 
T2[theory/architecture.md&lt;br&gt;Model architecture]

T1 --&gt; T2

%% === Source Code Layer ===
subgraph SRC[ src/efc/ ]
    C1[efc_core.py&lt;br&gt;core model]
    C2[efc_potential.py&lt;br&gt;energy-flow potential]
    C3[efc_entropy.py&lt;br&gt;entropy field + gradient]
    C4[efc_validation.py&lt;br&gt;astro validation tools]
end

T2 --&gt; SRC

%% === Scripts ===
subgraph SCRIPTS[ scripts/ ]
    S1[run_efc_baseline.py&lt;br&gt;baseline runs]
    S2[validate_efc.py&lt;br&gt;JWST / DESI / SPARC]
    S3[check_imports.py&lt;br&gt;import test gate]
    S4[update_efc_api.py&lt;br&gt;generate api/v1/]
end

SRC --&gt; S1
SRC --&gt; S2
SRC --&gt; S3
SRC --&gt; S4

%% === Data ===
subgraph DATA[data/ + external]
    D1[JWST catalogs]
    D2[DESI / BAO data]
    D3[SPARC rotation curves]
end

D1 --&gt; S2
D2 --&gt; S2
D3 --&gt; S2

S2 --&gt; OUT1[output/validation/&lt;br&gt;figures + metrics]
S1 --&gt; OUT2[output/baseline/]

%% === Semantics ===
subgraph SEM[Semantic Layer]
    SC1[schema/concepts.json&lt;br&gt;concept graph]
    SC2[schema/site-graph.json&lt;br&gt;Auth node and site map]
    SC3[figshare-index.json&lt;br&gt;DOI links]
    SC4[methodology/&lt;br&gt;Open method &amp; symbiosis]
end

SC1 --&gt; S4
S4 --&gt; API[api/v1/&lt;br&gt;JSON-LD endpoints]

%% === Open Science ===
OUT1 --&gt; FS[Export to Figshare]
OUT2 --&gt; FS
SC1 --&gt; FS
SC3 --&gt; FS

FS --&gt; DOI[Figshare DOIs]

%% === Reflection Layer ===
API --&gt; REF[reflection/&lt;br&gt;symbiosis + meta-analysis]
T1 --&gt; REF
SC2 --&gt; REF
FS --&gt; REF
</code></pre>

<h2>📅 Last Updated</h2>
<p>Automatically updated by <code>update-readme-date.yml</code>.</p>

</body>
</html>

# EFC Architecture Overview

## Layers
1. **Semantic Layer**
   - concepts.json
   - site-graph.json
   - methodology index
   - docs-index.json

2. **Computational Layer**
   - efc_core.py
   - efc_entropy.py
   - efc_potential.py
   - validation scripts

3. **Automation Layer**
   - update-schema.yml
   - update_efc_system.yml
   - run-validation.yml
   - export_figshare.yml

4. **Data Layer**
   - data/raw
   - data/processed
   - output/

5. **Integration Layer**
   - WordPress JSON-LD loader
   - Figshare DOI metadata
   - GitHub actions

## Flow
GitHub → Schema → API → Validation → Figshare → WordPress → Reflection → Update

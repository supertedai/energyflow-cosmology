# GitHub Workflows Overview

## 1. update-schema.yml
- Validates schema files
- Fetches sitemap.xml
- Updates site-graph.json

## 2. update_efc_system.yml
- Fetch Figshare metadata
- Merge with concepts.json
- Rebuild API under api/v1/

## 3. run-validation.yml
- Runs JWST / DESI / SPARC validation
- Generates figures
- Does not commit output/

## 4. export_figshare.yml
- Uploads updated results to DOI 30478916
- Requires secrets:
  - FIGSHARE_API_TOKEN
  - FIGSHARE_ARTICLE_ID

## 5. update-readme-date.yml
- Auto-updates timestamp in README.md

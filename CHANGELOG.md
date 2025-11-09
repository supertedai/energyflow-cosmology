# 🧭 CHANGELOG – Energy-Flow Cosmology (EFC)

This document tracks all major technical and structural updates to the Energy-Flow Cosmology repository, 
including schema integration, GitHub–WordPress synchronization, and semantic web enhancements.

---

## v1.1 – Semantic Integration and GitHub–WordPress Bridge  
**Date:** 2025-11-09  
**Author:** Morten Magnusson

### Overview
Full integration between GitHub repository and WordPress front-end via JSON-LD schema injection.

### Implemented
- Added dynamic JSON-LD schema loading from GitHub:
  ```php
  function efc_load_schema_from_github() {
    $url = 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/site-graph.json';
    $response = wp_remote_get($url);
    if (is_array($response) && !is_wp_error($response)) {
      echo '<script type="application/ld+json">' . $response['body'] . '</script>';
    }
  }
  add_action('wp_head', 'efc_load_schema_from_github');

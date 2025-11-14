<?php
/**
 * Core loader for the EFC Schema Loader plugin.
 * Fetches all schema JSON from GitHub and prints JSON-LD in <head>.
 */

if (!defined('EFC_CACHE_LIFETIME')) {
    define('EFC_CACHE_LIFETIME', 12 * HOUR_IN_SECONDS);
}

/**
 * List of all schema sources.
 */
function efc_all_schema_sources() {
    return [

        // Core Graph
        "concepts"        => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/schema/concepts.json",
        "docs-index"      => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/schema/docs-index.json",
        "methodology"     => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/schema/methodology-index.json",
        "site-graph"      => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/schema/site-graph.json",
        "schema-map"      => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/schema/schema-map.json",

        // Reflection Layer
        "reflection-schema" => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/reflection/reflection-schema.json",
        "resonance-links"   => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/reflection/resonance-links.json",
        "state-map"         => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/reflection/state-map.json",

        // Figshare Layer
        "figshare-index" => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/figshare/figshare-index.json",
        "figshare-links" => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/figshare/figshare-links.json",

        // API v1
        "api-metadata"    => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/metadata.json",
        "api-terms"       => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/terms.json",
        "api-methodology" => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/methodology.json",
        "api-concepts"    => "https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/concepts.json"
    ];
}

/**
 * Fetch a schema file, validate JSON, wrap as <script type="application/ld+json">.
 */
function efc_fetch_remote_schema($url) {
    $resp = wp_remote_get($url, ['timeout' => 6]);

    if (is_wp_error($resp)) {
        return "";
    }

    if (wp_remote_retrieve_response_code($resp) !== 200) {
        return "";
    }

    $body = trim(wp_remote_retrieve_body($resp));

    if ($body === "" || strpos($body, "{") === false) {
        return "";
    }

    json_decode($body);
    if (json_last_error() !== JSON_ERROR_NONE) {
        return "";
    }

    return "<script type=\"application/ld+json\">\n$body\n</script>\n";
}

/**
 * Print FULL schema bundle into <head>.
 */
function efc_output_full_schema_bundle() {

    $cached = get_transient('efc_full_schema_bundle');
    if ($cached !== false) {
        echo $cached;
        return;
    }

    $out = "\n<!-- EFC FULL SCHEMA GRAPH BEGIN -->\n";

    foreach (efc_all_schema_sources() as $key => $url) {
        $json = efc_fetch_remote_schema($url);
        if ($json !== "") {
            $out .= "\n<!-- EFC: $key -->\n$json";
        }
    }

    $out .= "<!-- EFC FULL SCHEMA GRAPH END -->\n";

    set_transient('efc_full_schema_bundle', $out, EFC_CACHE_LIFETIME);

    echo $out;
}
add_action('wp_head', 'efc_output_full_schema_bundle', 2);


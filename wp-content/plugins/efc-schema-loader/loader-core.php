<?php
/**
 * Core schema loader for EFC Schema Loader plugin.
 */

// Cache lifetime (12 timer)
if (!defined('EFC_CACHE_LIFETIME')) {
    define('EFC_CACHE_LIFETIME', 12 * HOUR_IN_SECONDS);
}

/**
 * Full liste over schema-kilder i GitHub-repoet.
 */
function efc_all_schema_sources() {
    return array(

        // CORE GRAPH
        'concepts'        => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/schema/concepts.json',
        'docs-index'      => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/schema/docs-index.json',
        'methodology'     => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/schema/methodology-index.json',
        'site-graph'      => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/schema/site-graph.json',
        'schema-map'      => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/schema/schema-map.json',

        // REFLECTION LAYER
        'reflection-schema' => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/reflection/reflection-schema.json',
        'resonance-links'   => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/reflection/resonance-links.json',
        'state-map'         => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/reflection/state-map.json',

        // FIGSHARE LAYER
        'figshare-index'  => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/figshare/figshare-index.json',
        'figshare-links'  => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/figshare/figshare-links.json',

        // API V1
        'api-metadata'    => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/metadata.json',
        'api-terms'       => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/terms.json',
        'api-methodology' => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/methodology.json',
        'api-concepts'    => 'https://raw.githubusercontent.com/supertedai/energyflow-cosmology/main/api/v1/concepts.json',
    );
}

/**
 * Henter én schema-fil, validerer JSON og pakker inn som JSON-LD script.
 */
function efc_fetch_remote_schema($url) {
    $response = wp_remote_get($url, array('timeout' => 5));

    if (is_wp_error($response)) {
        return '';
    }

    if (wp_remote_retrieve_response_code($response) !== 200) {
        return '';
    }

    $body = trim(wp_remote_retrieve_body($response));

    if ($body === '' || strpos($body, '{') === false) {
        return '';
    }

    json_decode($body);
    if (json_last_error() !== JSON_ERROR_NONE) {
        return '';
    }

    return "<script type=\"application/ld+json\">\n" . $body . "\n</script>\n";
}

/**
 * Hoved-funksjon som skriver hele schema-grafen i <head>.
 */
function efc_output_full_schema_bundle() {
    $cached = get_transient('efc_full_schema_bundle');
    if ($cached !== false) {
        echo $cached;
        return;
    }

    $sources = efc_all_schema_sources();
    $out = "\n<!-- EFC FULL SCHEMA GRAPH BEGIN -->\n";

    foreach ($sources as $key => $url) {
        $jsonld = efc_fetch_remote_schema($url);
        if ($jsonld !== '') {
            $out .= "\n<!-- EFC: " . esc_html($key) . " -->\n" . $jsonld;
        }
    }

    $out .= "<!-- EFC FULL SCHEMA GRAPH END -->\n";

    set_transient('efc_full_schema_bundle', $out, EFC_CACHE_LIFETIME);

    echo $out;
}
add_action('wp_head', 'efc_output_full_schema_bundle', 2);

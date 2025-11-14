<?php
/**
 * WP-CLI integration for EFC Schema Loader
 */

if (!defined('ABSPATH')) {
    exit;
}

class EFC_CLI_Commands {

    /**
     * Clear schema cache.
     *
     * ## EXAMPLES
     *
     *     wp efc:refresh-schema
     */
    public function refresh_schema($args, $assoc_args) {
        delete_transient('efc_full_schema_bundle');
        WP_CLI::success('EFC schema cache cleared. It will be rebuilt on next page load.');
    }

    /**
     * Validate all schema sources.
     *
     * ## EXAMPLES
     *
     *     wp efc:validate-schema
     */
    public function validate_schema($args, $assoc_args) {
        $sources = efc_all_schema_sources();
        foreach ($sources as $key => $url) {
            $resp = wp_remote_get($url, array('timeout' => 5));
            if (is_wp_error($resp)) {
                WP_CLI::warning("$key => WP Error");
                continue;
            }
            if (wp_remote_retrieve_response_code($resp) !== 200) {
                WP_CLI::warning("$key => HTTP " . wp_remote_retrieve_response_code($resp));
                continue;
            }
            json_decode(wp_remote_retrieve_body($resp));
            if (json_last_error() === JSON_ERROR_NONE) {
                WP_CLI::log("$key => OK");
            } else {
                WP_CLI::warning("$key => Invalid JSON");
            }
        }
        WP_CLI::success('Validation run complete.');
    }
}

WP_CLI::add_command('efc', 'EFC_CLI_Commands');

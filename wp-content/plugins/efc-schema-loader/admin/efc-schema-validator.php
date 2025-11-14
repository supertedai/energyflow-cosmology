<?php
/**
 * EFC Schema Validator — Admin Dashboard
 */

add_action('admin_menu', function () {
    add_menu_page(
        'EFC Schema Validator',
        'EFC Schema',
        'manage_options',
        'efc-schema-validator',
        'efc_admin_schema_dashboard',
        'dashicons-chart-network',
        40
    );
});

function efc_admin_schema_dashboard() {
    $sources = efc_all_schema_sources();

    echo "<div class='wrap'><h1>EFC Schema Validator</h1>";

    echo "<table class='widefat'><thead><tr>
            <th>Key</th><th>URL</th><th>Status</th>
          </tr></thead><tbody>";

    foreach ($sources as $key => $url) {
        $start = microtime(true);
        $resp  = wp_remote_get($url, array('timeout' => 5));
        $time  = round((microtime(true) - $start) * 1000, 2);

        if (is_wp_error($resp)) {
            $status = "<span style='color:red'>WP Error</span>";
        } elseif (wp_remote_retrieve_response_code($resp) !== 200) {
            $status = "<span style='color:red'>HTTP " . wp_remote_retrieve_response_code($resp) . "</span>";
        } else {
            json_decode(wp_remote_retrieve_body($resp));
            $status = (json_last_error() === JSON_ERROR_NONE)
                ? "<span style='color:green'>Valid JSON ({$time} ms)</span>"
                : "<span style='color:red'>Invalid JSON</span>";
        }

        echo "<tr><td>" . esc_html($key) . "</td><td><a href='" . esc_url($url) . "' target='_blank'>" . esc_html($url) . "</a></td><td>{$status}</td></tr>";
    }

    echo "</tbody></table></div>";
}

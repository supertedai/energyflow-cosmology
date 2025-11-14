<?php
/**
 * EFC Schema Validator — Admin Dashboard
 */

if (!defined('ABSPATH')) {
    exit;
}

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
    if (!function_exists('efc_all_schema_sources')) {
        echo '<div class="notice notice-error"><p>efc_all_schema_sources() not available. Check loader-core.php.</p></div>';
        return;
    }

    $sources = efc_all_schema_sources();

    echo '<div class="wrap">';
    echo '<h1>EFC Schema Validator</h1>';
    echo '<p>This dashboard checks each schema source in the EFC GitHub repository and validates JSON.</p>';

    echo '<table class="widefat fixed striped">';
    echo '<thead><tr>
            <th>Key</th>
            <th>URL</th>
            <th>Status</th>
          </tr></thead><tbody>';

    foreach ($sources as $key => $url) {
        $start = microtime(true);
        $resp  = wp_remote_get($url, array('timeout' => 5));
        $time  = round((microtime(true) - $start) * 1000, 2);

        if (is_wp_error($resp)) {
            $status = '<span style="color:red">WP_Error: ' . esc_html($resp->get_error_message()) . '</span>';
        } elseif (wp_remote_retrieve_response_code($resp) !== 200) {
            $status = '<span style="color:red">HTTP ' . intval(wp_remote_retrieve_response_code($resp)) . '</span>';
        } else {
            $body = wp_remote_retrieve_body($resp);
            json_decode($body);
            if (json_last_error() === JSON_ERROR_NONE) {
                $status = '<span style="color:green">Valid JSON (' . $time . ' ms)</span>';
            } else {
                $status = '<span style="color:red">Invalid JSON (' . $time . ' ms)</span>';
            }
        }

        echo '<tr>';
        echo '<td>' . esc_html($key) . '</td>';
        echo '<td><a href="' . esc_url($url) . '" target="_blank" rel="noopener noreferrer">' . esc_html($url) . '</a></td>';
        echo '<td>' . $status . '</td>';
        echo '</tr>';
    }

    echo '</tbody></table></div>';
}

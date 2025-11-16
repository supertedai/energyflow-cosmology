<?php
/**
 * Plugin Name: EFC Schema Loader
 * Description: Loads Energy-Flow Cosmology schema from GitHub into WordPress and provides admin validation tools & CLI commands.
 * Version: 1.0.0
 * Author: Morten Magnusson
 * Text Domain: efc-schema-loader
 */

// Exit if accessed directly
if (!defined('ABSPATH')) exit;

// Load core schema loader (injects JSON-LD into <head>)
require_once __DIR__ . '/loader-core.php';

// Admin dashboard (schema validator)
if (is_admin()) {
    require_once __DIR__ . '/admin/efc-schema-validator.php';
}

// WP-CLI integration (optional)
if (defined('WP_CLI') && WP_CLI) {
    require_once __DIR__ . '/includes/class-efc-cli.php';
}

// GitHub webhook handler (for auto cache purge)
require_once __DIR__ . '/includes/webhook-handler.php';

<?php
/**
 * Plugin Name: EFC Schema Loader
 * Description: Loads Energy-Flow Cosmology schema from GitHub and provides admin validation dashboard.
 * Version: 1.0.0
 * Author: Morten Magnusson
 */

if (!defined('ABSPATH')) exit;

// Load core loader functions (you can move your existing functions.php logic here later)
require_once __DIR__ . '/loader-core.php';

// Load admin validator
if (is_admin()) {
    require_once __DIR__ . '/admin/efc-schema-validator.php';
}

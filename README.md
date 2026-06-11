# NetBox IP Prefix Tree

A NetBox plugin that provides a hierarchical tree view for IP prefixes.

`netbox-ipprefix-tree` displays NetBox prefixes in an expandable and collapsible tree structure, making it easier to browse large IP address plans, especially in environments containing many nested prefixes across one or more VRFs.

The plugin builds and caches parent/child prefix relationships in a dedicated database table, allowing the interface to remain responsive even when NetBox contains thousands of prefixes.

## Features

- Hierarchical tree view of NetBox IP prefixes
- Expandable and collapsible prefix rows
- VRF-aware display
  - If multiple VRFs are present, each VRF is shown as a root node
  - If only one VRF or the global VRF is present, prefixes are shown directly at the root
- Utilises a similar table layout to the IP Prefixes page, but with smaller prefix height to display more prefixes on the screen
- Search by prefix or description with automatic expansion of matching search results and highlighting of matched prefixes
- Cached prefix hierarchy table for improved performance
- Automatic rebuild of the prefix hierarchy table when prefixes are added, updated or deleted

## Requirements

- NetBox 4.5.x or later
- Python 3.12 or later
- PostgreSQL
- PostgreSQL extensions:
  - `pg_trgm`
  - `btree_gist`

The plugin is currently intended for use with NetBox 4.5.x. Compatibility with earlier or later NetBox versions should be tested before production use.

## Installation

Install the package into the NetBox virtual environment:

If installing from a local source directory:

```bash
cd /path/to/netbox-ipprefix-tree
sudo /opt/netbox/venv/bin/pip install .
```

## Enable the Plugin

Edit the NetBox configuration file, this is usually:

```bash
/opt/netbox/netbox/netbox/configuration.py
```

Add the plugin to the `PLUGINS` list:

```python
PLUGINS = [
    "netbox_ipprefix_tree",
]
```

No plugin-specific configuration is currently required.

## Run Database Migrations

After installing and enabling the plugin, run NetBox migrations:

```bash
sudo /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py migrate
```

The migrations will create the prefix hierarchy tables, indexes and database triggers.

## Collect Static Files

Collect static files so NetBox can serve the plugin JavaScript, CSS, and icons:

```bash
sudo /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py collectstatic --no-input
```

## Restart NetBox Services

Restart NetBox and the NetBox RQ worker:

```bash
sudo systemctl restart netbox netbox-rq
```

Depending on your deployment, you may also need to restart your web server or application service.

## Initial Hierarchy Build

The plugin uses a cached hierarchy table to store the parent/child relationships of prefixes.

After installation, run the initial hierarchy rebuild:

```bash
sudo /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py rebuild_prefix_hierarchy --force
```

This populates the plugin hierarchy table from the existing prefixes in NetBox.


## How the Hierarchy Cache Works

The plugin maintains a cached hierarchy table containing direct parent/child prefix relationships.

For example:

```text
10.0.0.0/8
└── 10.1.0.0/16
    ├── 10.1.1.0/24
    ├── 10.1.2.0/24
    └── 10.1.3.0/24
```

The cache allows the plugin to quickly retrieve only the direct children of an expanded prefix, rather than recalculating prefix relationships on every page request.

When prefixes are added, changed, or deleted, database triggers mark the hierarchy as dirty. A background rebuild process then rebuilds the hierarchy table.

The rebuild process creates a replacement hierarchy table first, then swaps it into place. This allows the existing tree to remain available while the rebuild is running.

## Rebuilding the Prefix Hierarchy

To manually rebuild the hierarchy:

```bash
sudo /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py rebuild_prefix_hierarchy --force
```

This may be useful after:

- Bulk prefix imports
- Manual database changes
- Plugin upgrades
- Troubleshooting hierarchy display issues

## AI-Assisted Development Disclosure

Portions of this plugin were developed with assistance from AI-based coding tools.

AI assistance was used to help with:

- SQL query review and optimisation
- CSS generation
- Documentation drafting

All AI-generated or AI-assisted code should be reviewed, tested and validated before use in production environments.

## Operational Notes

This plugin is designed to improve navigation of large prefix datasets, but it should still be tested with your own NetBox data before production deployment.

For large environments, it is recommended to test:

- Initial hierarchy rebuild time
- Search performance
- Browser performance with large expanded sections
- Behaviour after bulk prefix imports
- Behaviour across multiple VRFs

## License

This project is licensed under the Apache License 2.0.

You may use, modify, and redistribute this project, including as part of commercial or proprietary works, subject to the terms of the Apache License 2.0.

Derivative works must preserve applicable copyright, licence and notice information.

See `LICENSE` and `NOTICE` for details.

## Author

Rohan Wallace

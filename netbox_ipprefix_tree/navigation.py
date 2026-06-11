from netbox.plugins import PluginMenu, PluginMenuItem


menu = PluginMenu(
    label="IP Prefix Tree",
    groups=(
        (
            "Prefixes",
            (
                PluginMenuItem(
                    link="plugins:netbox_ipprefix_tree:prefix_tree",
                    link_text="Prefix Tree",
                ),
            ),
        ),
    ),
)

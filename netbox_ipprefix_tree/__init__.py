from netbox.plugins import PluginConfig


__version__ = "0.1.3"

class IPPrefixTreeConfig(PluginConfig):
    name = "netbox_ipprefix_tree"
    verbose_name = "IP Prefix Tree"
    description = "Hierarchical IP prefix tree"
    version = __version__
    base_url = "ipprefix-tree"
    urls = "netbox_ipprefix_tree.urls"
    min_version = "4.5.0"

    def ready(self):
        super().ready()
        from . import signals as _signals  # noqa: F401


config = IPPrefixTreeConfig

default_app_config = "netbox_ipprefix_tree.apps.NetboxIpPrefixTreeConfig"

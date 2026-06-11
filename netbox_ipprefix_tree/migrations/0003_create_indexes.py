from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_ipprefix_tree", "0002_create_tables"),
    ]

    operations = [
        #
        # ipam_prefix indexes
        #
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS
                ipam_prefix_prefix_gist
            ON ipam_prefix
            USING GIST (
                prefix inet_ops
            );
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS
                ipam_prefix_prefix_gist;
            """,
        ),
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS
                ipam_prefix_vrf_id_idx
            ON ipam_prefix (
                vrf_id
            );
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS
                ipam_prefix_vrf_id_idx;
            """,
        ),
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS
                ipam_prefix_vrf_family_prefix_idx
            ON ipam_prefix (
                vrf_id,
                family(prefix),
                prefix
            );
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS
                ipam_prefix_vrf_family_prefix_idx;
            """,
        ),
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS
                ipam_prefix_prefix_text_trgm_idx
            ON ipam_prefix
            USING GIN (
                (prefix::text) gin_trgm_ops
            );
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS
                ipam_prefix_prefix_text_trgm_idx;
            """,
        ),
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS
                ipam_prefix_description_trgm_idx
            ON ipam_prefix
            USING GIN (
                description gin_trgm_ops
            );
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS
                ipam_prefix_description_trgm_idx;
            """,
        ),
        #
        # hierarchy indexes
        #
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS
                netbox_ipprefix_tree_hierarchy_parent_child_idx
            ON netbox_ipprefix_tree_hierarchy (
                parent_prefix_id,
                child_prefix_id
            );
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS
                netbox_ipprefix_tree_hierarchy_parent_child_idx;
            """,
        ),
        migrations.RunSQL(
            sql="""
            CREATE UNIQUE INDEX IF NOT EXISTS
                netbox_ipprefix_tree_hierarchy_child_unique_idx
            ON netbox_ipprefix_tree_hierarchy (
                child_prefix_id
            );
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS
                netbox_ipprefix_tree_hierarchy_child_unique_idx;
            """,
        ),
    ]

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("netbox_ipprefix_tree", "0003_create_indexes"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION netbox_ipprefix_tree_refresh_trigger()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                UPDATE
                    netbox_ipprefix_tree_rebuild_state
                SET
                    dirty = TRUE,
                    updated = NOW()
                WHERE
                    id = 1;

                RETURN NULL;
            END;
            $$;

            DROP TRIGGER IF EXISTS
                netbox_ipprefix_tree_prefix_insert_refresh
            ON ipam_prefix;

            DROP TRIGGER IF EXISTS
                netbox_ipprefix_tree_prefix_update_refresh
            ON ipam_prefix;

            DROP TRIGGER IF EXISTS
                netbox_ipprefix_tree_prefix_delete_refresh
            ON ipam_prefix;

            CREATE TRIGGER
                netbox_ipprefix_tree_prefix_insert_refresh
            AFTER INSERT ON ipam_prefix
            FOR EACH STATEMENT
            EXECUTE FUNCTION netbox_ipprefix_tree_refresh_trigger();

            CREATE TRIGGER
                netbox_ipprefix_tree_prefix_update_refresh
            AFTER UPDATE ON ipam_prefix
            FOR EACH STATEMENT
            EXECUTE FUNCTION netbox_ipprefix_tree_refresh_trigger();

            CREATE TRIGGER
                netbox_ipprefix_tree_prefix_delete_refresh
            AFTER DELETE ON ipam_prefix
            FOR EACH STATEMENT
            EXECUTE FUNCTION netbox_ipprefix_tree_refresh_trigger();
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS
                netbox_ipprefix_tree_prefix_insert_refresh
            ON ipam_prefix;

            DROP TRIGGER IF EXISTS
                netbox_ipprefix_tree_prefix_update_refresh
            ON ipam_prefix;

            DROP TRIGGER IF EXISTS
                netbox_ipprefix_tree_prefix_delete_refresh
            ON ipam_prefix;

            DROP FUNCTION IF EXISTS
                netbox_ipprefix_tree_refresh_trigger();
            """,
        ),
    ]

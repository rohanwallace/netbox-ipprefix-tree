from django.db import migrations


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                  CREATE EXTENSION IF NOT EXISTS btree_gist;
                EXCEPTION
                  WHEN insufficient_privilege THEN
                    RAISE WARNING 'Missing privilege to create btree_gist extension. Run manually: psql -U postgres -d netbox -c "CREATE EXTENSION btree_gist;"';
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                  CREATE EXTENSION IF NOT EXISTS pg_trgm;
                EXCEPTION
                  WHEN insufficient_privilege THEN
                    RAISE WARNING 'Missing privilege to create pg_trgm extension. Run manually: psql -U postgres -d netbox -c "CREATE EXTENSION pg_trgm;"';
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

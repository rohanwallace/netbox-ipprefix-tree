from django.core.management import call_command


def rebuild_prefix_hierarchy_job():
    call_command("rebuild_prefix_hierarchy")

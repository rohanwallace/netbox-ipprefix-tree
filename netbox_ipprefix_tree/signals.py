from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from ipam.models import Prefix
import django_rq


def enqueue_prefix_hierarchy_rebuild():
    """
    Queue a hierarchy rebuild after the current database transaction commits.

    The database trigger is responsible for marking the hierarchy dirty.
    This signal is only responsible for waking up the rebuild worker.
    """

    def _enqueue():
        queue = django_rq.get_queue("default")

        queue.enqueue(
            "django.core.management.call_command",
            "rebuild_prefix_hierarchy",
            job_timeout=3600,
        )

    transaction.on_commit(_enqueue)


@receiver(post_save, sender=Prefix)
def prefix_saved(sender, instance, **kwargs):
    enqueue_prefix_hierarchy_rebuild()


@receiver(post_delete, sender=Prefix)
def prefix_deleted(sender, instance, **kwargs):
    enqueue_prefix_hierarchy_rebuild()

import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from ipam.models import Prefix
from netbox.tables import NetBoxTable, columns


class PrefixTreeTable(NetBoxTable):
    """Restricted prefix table for the left-hand prefix tree pane.

    Only these columns are intentionally exposed:

    - prefix
    - description
    - status
    - utilization

    The prefix column is forced to remain visible and first, because the
    expand/collapse tree controls are rendered inside that column.
    """

    prefix = tables.Column(
        accessor="prefix",
        verbose_name=_("Prefix"),
        attrs={
            "td": {
                "class": "text-nowrap",
            },
        },
    )

    description = tables.Column(
        accessor="description",
        verbose_name=_("Description"),
    )

    status = columns.ChoiceFieldColumn(
        verbose_name=_("Status"),
    )

    utilization = columns.UtilizationColumn(
        accessor="get_utilization",
        verbose_name=_("Utilization"),
        orderable=False,
    )

    class Meta(NetBoxTable.Meta):
        model = Prefix
        fields = (
            "prefix",
            "description",
            "status",
            "utilization",
        )
        default_columns = (
            "prefix",
            "description",
        )
        exclude = (
            "pk",
            "id",
            "actions",
        )

    def _set_columns(self, selected_columns):
        """Keep prefix visible and first, regardless of table config.

        NetBox's standard table config UI lets users move/remove columns.
        For this tree view, hiding the prefix column would break the UI, so
        we force it back in and keep it as the first displayed column.
        """

        selected_columns = list(selected_columns or self.Meta.default_columns)

        selected_columns = [
            column
            for column in selected_columns
            if column in self.Meta.fields
        ]

        selected_columns = [
            "prefix",
            *[
                column
                for column in selected_columns
                if column != "prefix"
            ],
        ]

        super()._set_columns(selected_columns)
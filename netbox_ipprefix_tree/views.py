from django.views.generic import TemplateView
from django.views import View
from django.http import Http404, HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.db import connection
from ipam.models import Prefix, VRF
from ipam.tables import AnnotatedIPAddressTable
from ipam.utils import annotate_ip_space
from .tables import PrefixTreeTable


GLOBAL_VRF_ID = "global"
GLOBAL_VRF_NAME = "(Global)"

def configure_table(table, request):
    """Apply NetBox/django-tables2 request configuration when available."""

    if hasattr(table, "configure"):
        table.configure(request)

    return table


def build_prefix_tree_table(qs, request):
    """Build the restricted, configurable tree table used in the left pane."""

    table = PrefixTreeTable(qs)
    table = configure_table(table, request)

    return table


def get_prefix_utilisation(prefix):
    """Return prefix utilisation percentage as a float roudned to 1 decimal place."""

    utilisation = None

    if hasattr(prefix, "get_utilisation"):
        utilisation = prefix.get_utilisation()
    elif hasattr(prefix, "utilisation"):
        utilisation = prefix.utilisation

    if utilisation is None:
        return None

    try:
        return round(float(utilisation), 1)
    except (TypeError, ValueError):
        return None


def format_percent(value):
    """Format a percentage like NetBox does: 14% or 13.7%."""

    if value is None:
        return None

    if float(value).is_integer():
        return f"{int(value)}%"

    return f"{value:.1f}%"

def build_prefix_ipaddress_table(prefix, request):
    """Build the native NetBox-style IP address table for a prefix.

    This mirrors the behaviour of NetBox's native prefix IP addresses tab by
    using AnnotatedIPAddressTable with annotate_ip_space().  This gives us
    normal IP address rows plus NetBox's synthetic available-space rows.
    """

    table = AnnotatedIPAddressTable(
        data=annotate_ip_space(prefix),
        orderable=False,
    )
    table.configure(request)

    return table

class PrefixTreeView(TemplateView):
    template_name = "netbox_ipprefix_tree/prefix_tree.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        table = build_prefix_tree_table(Prefix.objects.none(), self.request)
        vrf_list = []

        # Create a VRF to represent the Global Table VRF (null VRF in the DB)
        if Prefix.objects.filter(vrf__isnull=True).exists():
            vrf_list.append(
                {
                    "id": GLOBAL_VRF_ID,
                    "name": GLOBAL_VRF_NAME,
                }
            )

        # Real VRFs
        for vrf in (
            VRF.objects.filter(prefixes__isnull=False).distinct().order_by("name")
        ):
            vrf_list.append(
                {
                    "id": str(vrf.id),
                    "name": vrf.name,
                }
            )

        multiple_vrfs = len(vrf_list) > 1
        context["table"] = table
        context["vrf_list"] = vrf_list
        context["multiple_vrfs"] = multiple_vrfs
        context["single_vrf_id"] = GLOBAL_VRF_ID

        # Single VRF optimization
        if not multiple_vrfs and vrf_list:
            #single_vrf_id = vrf_list[0]["id"]
            #context["single_vrf_id"] = single_vrf_id
            #roots = get_children(prefix=None, vrf=single_vrf_id)
            roots = get_children(prefix=None, vrf=GLOBAL_VRF_ID)
            context["table"] = build_prefix_tree_table(roots, self.request)

        return context


class VRFListView(View):
    def get(self, request):

        vrfs = []

        if Prefix.objects.filter(vrf__isnull=True).exists():
            vrfs.append(
                {
                    "id": GLOBAL_VRF_ID,
                    "name": GLOBAL_VRF_NAME,
                }
            )

        for vrf in (VRF.objects.filter(prefixes__isnull=False).distinct().order_by("name")):
            vrfs.append(
                {
                    "id": str(vrf.id),
                    "name": vrf.name,
                }
            )

        return JsonResponse(vrfs, safe=False)


def get_children(prefix=None, vrf=None):
    """Return only direct hierarchical children using precomputed hierarchy table"""

    is_global = vrf == GLOBAL_VRF_ID

    with connection.cursor() as cursor:
        if is_global:
            vrf_condition = "p.vrf_id IS NULL"
            vrf_param = None
        else:
            vrf_condition = "p.vrf_id = %s"
            vrf_param = vrf

        if prefix is None:
            # Root prefixes
            cursor.execute(
                f"""
                SELECT
                    p.id,
                    EXISTS (
                        SELECT 1
                        FROM netbox_ipprefix_tree_hierarchy h
                        WHERE h.parent_prefix_id = p.id
                    ) AS has_children
                FROM ipam_prefix p
                WHERE
                    {vrf_condition}
                    AND NOT EXISTS (
                        SELECT 1
                        FROM netbox_ipprefix_tree_hierarchy h
                        WHERE h.child_prefix_id = p.id
                    )
                ORDER BY
                    family(p.prefix),
                    p.prefix
                """,
                [vrf_param] if vrf_param is not None else [],
            )
        else:
            # Child prefixes
            cursor.execute(
                f"""
                SELECT
                    p.id,
                    EXISTS (
                        SELECT 1
                        FROM netbox_ipprefix_tree_hierarchy h2
                        WHERE h2.parent_prefix_id = p.id
                    ) AS has_children
                FROM ipam_prefix p
                JOIN netbox_ipprefix_tree_hierarchy h
                    ON h.child_prefix_id = p.id
                JOIN ipam_prefix parent
                    ON parent.id = h.parent_prefix_id
                WHERE
                    parent.prefix = %s
                    AND {vrf_condition}
                ORDER BY
                    family(p.prefix),
                    p.prefix
                """,
                [prefix, vrf_param] if vrf_param is not None else [prefix],
            )

        rows = cursor.fetchall()

    ids = [r[0] for r in rows]

    qs = Prefix.objects.filter(id__in=ids)

    prefix_map = {p.id: p for p in qs}

    ordered = []

    for row in rows:
        prefix_id = row[0]
        has_children = row[1]
        obj = prefix_map[prefix_id]
        obj.has_children = has_children
        ordered.append(obj)

    return ordered


class PrefixChildrenView(View):
    def get(self, request):
        parent = request.GET.get("parent")
        vrf = request.GET.get("vrf")
        depth = int(request.GET.get("depth", 0))

        if parent == "":
            parent = None

        qs = get_children(parent, vrf)

        table = build_prefix_tree_table(qs, request)

        html = render_to_string(
            "netbox_ipprefix_tree/prefix_rows.html",
            {
                "table": table,
                "depth": depth,
                "vrf": vrf,
            },
            request=request,
        )

        return HttpResponse(html)


class PrefixDetailView(View):
    """Return the right-pane detail HTML for a selected prefix."""

    def get(self, request, pk):
        queryset = Prefix.objects.all()

        if hasattr(queryset, "restrict"):
            queryset = queryset.restrict(request.user, "view")

        try:
            prefix = (
                queryset.select_related(
                    "vlan",
                    "tenant",
                    "role",
                    "vrf",
                    "scope_type",
                ).get(pk=pk)
            )
        except Prefix.DoesNotExist as exc:
            raise Http404("Prefix not found") from exc

        utilisation = get_prefix_utilisation(prefix)
        ipaddress_table = build_prefix_ipaddress_table(prefix, request)

        html = render_to_string(
            "netbox_ipprefix_tree/prefix_detail.html",
            {
                "object": prefix,
                "prefix": prefix,
                "utilisation": utilisation,
                "utilisation_display": format_percent(utilisation),
                "ipaddress_table": ipaddress_table,
            },
            request=request,
        )

        return HttpResponse(html)


class PrefixSearchView(View):
    def get(self, request):

        q = request.GET.get("q", "").strip()

        if not q:
            return JsonResponse([], safe=False)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.id,
                    p.prefix::text,
                    COALESCE(p.description, ''),
                    COALESCE(p.vrf_id::text, %s)
                FROM ipam_prefix p
                WHERE
                    p.prefix::text ILIKE %s
                    OR p.description ILIKE %s
                ORDER BY
                    family(p.prefix),
                    p.prefix
                LIMIT 100
                """,
                [GLOBAL_VRF_ID, f"%{q}%", f"%{q}%"],
            )

            matches = cursor.fetchall()

        results = []

        for match in matches:
            prefix_id = match[0]
            prefix = match[1]
            description = match[2]
            vrf_id = match[3]

            path = []

            current_id = prefix_id

            while True:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT parent.id
                        FROM netbox_ipprefix_tree_hierarchy h
                        JOIN ipam_prefix parent
                            ON parent.id = h.parent_prefix_id
                        WHERE
                            h.child_prefix_id = %s
                        LIMIT 1
                        """,
                        [current_id],
                    )

                    row = cursor.fetchone()

                if not row:
                    break

                parent_id = row[0]

                path.insert(0, parent_id)

                current_id = parent_id

            results.append(
                {
                    "prefix_id": prefix_id,
                    "prefix": prefix,
                    "description": description,
                    "vrf_id": vrf_id,
                    "path": path,
                }
            )

        return JsonResponse(results, safe=False)

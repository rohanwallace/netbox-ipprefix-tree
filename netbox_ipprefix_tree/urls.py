from django.urls import path
from .views import (
    PrefixChildrenView,
    PrefixDetailView,
    PrefixSearchView,
    PrefixTreeView,
    VRFListView,
)


app_name = "netbox_ipprefix_tree"

urlpatterns = [
    path("prefix-tree/", PrefixTreeView.as_view(), name="prefix_tree"),
    path("api/children/", PrefixChildrenView.as_view(), name="prefix_children"),
    path("api/search/", PrefixSearchView.as_view(), name="prefix_search"),
    path("api/vrfs/", VRFListView.as_view(), name="vrf_list"),
    path("api/prefix/<int:pk>/", PrefixDetailView.as_view(), name="prefix_detail"),
]

const prefixCache = {};

const ICONS = {
    collapsed: "/static/netbox_ipprefix_tree/icons/collapsed.svg",
    expanded: "/static/netbox_ipprefix_tree/icons/expanded.svg",
    leaf: "/static/netbox_ipprefix_tree/icons/leaf.svg",
};

function makeCacheKey(vrfId, prefix) {
    return `${vrfId || "global"}:${prefix}`;
}

function getRowDepth(row) {
    return parseInt(row.dataset.depth, 10) || 0;
}

function updateIcon(row, expanded) {
    const icon = row.querySelector(".tree-expand-icon");

    if (!icon) {
        return;
    }

    const hasChildren = row.dataset.hasChildren === "true";

    if (!hasChildren) {
        icon.src = ICONS.leaf;
        return;
    }

    icon.src = expanded ? ICONS.expanded : ICONS.collapsed;
}

function updateCache(row, expanded) {
    const cacheKey = makeCacheKey(
        row.dataset.vrfId,
        row.dataset.prefix
    );

    prefixCache[cacheKey] = {
        expanded,
    };
}

function collapse(row, depth) {
    let next = row.nextElementSibling;

    while (next) {
        const nextDepth = getRowDepth(next);

        if (nextDepth <= depth) {
            break;
        }

        next.style.display = "none";
        next = next.nextElementSibling;
    }

    row.dataset.expanded = "false";
    updateCache(row, false);
    updateIcon(row, false);
}

function showExistingChildren(row, depth) {
    let next = row.nextElementSibling;
    const visibleDepths = {};

    visibleDepths[depth] = true;

    while (next) {
        const nextDepth = getRowDepth(next);

        if (nextDepth <= depth) {
            break;
        }

        const parentVisible = visibleDepths[nextDepth - 1] !== false;

        if (!parentVisible) {
            next.style.display = "none";
            visibleDepths[nextDepth] = false;
            next = next.nextElementSibling;
            continue;
        }

        next.style.display = "";

        const cacheKey = makeCacheKey(
            next.dataset.vrfId,
            next.dataset.prefix
        );

        const childExpanded =
            prefixCache[cacheKey] &&
            prefixCache[cacheKey].expanded === true;

        visibleDepths[nextDepth] = childExpanded;
        updateIcon(next, childExpanded);

        next = next.nextElementSibling;
    }
}

async function expand(row, parent, depth) {
    if (row.dataset.loading === "true") {
        return;
    }

    if (row.dataset.expanded === "true") {
        return;
    }

    if (row.dataset.loaded === "true") {
        showExistingChildren(row, depth);
        row.dataset.expanded = "true";
        updateCache(row, true);
        updateIcon(row, true);
        return;
    }

    row.dataset.loading = "true";

    const icon = row.querySelector(".tree-expand-icon");

    if (icon) {
        icon.style.opacity = "0.4";
    }

    try {
        const vrf = row.dataset.vrfId;
        const response = await fetch(
            `/plugins/ipprefix-tree/api/children/?parent=${encodeURIComponent(parent)}&vrf=${encodeURIComponent(vrf)}&depth=${depth + 1}`
        );

        if (!response.ok) {
            console.error(
                "Failed to load prefix children:",
                response.status
            );
            return;
        }

        const html = await response.text();

        if (row.dataset.expanded === "true") {
            return;
        }

        row.insertAdjacentHTML("afterend", html);
        row.dataset.loaded = "true";
        row.dataset.expanded = "true";
        updateCache(row, true);
        updateIcon(row, true);
    } finally {
        row.dataset.loading = "false";

        if (icon) {
            icon.style.opacity = "";
        }
    }
}

async function toggleRowExpansion(row) {
    if (row.dataset.loading === "true") {
        return;
    }

    const hasChildren = row.dataset.hasChildren === "true";

    if (!hasChildren) {
        return;
    }

    let prefix = row.dataset.prefix;

    if (row.dataset.nodeType === "vrf") {
        prefix = "";
    }

    const depth = getRowDepth(row);
    const expanded = row.dataset.expanded === "true";

    if (expanded) {
        collapse(row, depth);
        return;
    }

    await expand(row, prefix, depth);
}

function setSelectedRow(row) {
    document
        .querySelectorAll("tr.tree-row.tree-selected")
        .forEach(selectedRow => selectedRow.classList.remove("tree-selected"));

    row.classList.add("tree-selected");
}

async function loadPrefixDetail(row) {
    if (row.dataset.nodeType !== "prefix") {
        return;
    }

    const prefixId = row.dataset.prefixId;
    const detailPane = document.getElementById("prefix-detail-pane");

    if (!prefixId || !detailPane) {
        return;
    }

    setSelectedRow(row);
    detailPane.classList.add("prefix-detail-loading");

    try {
        const response = await fetch(
            `/plugins/ipprefix-tree/api/prefix/${encodeURIComponent(prefixId)}/`
        );

        if (!response.ok) {
            detailPane.innerHTML = `
                <div class="alert alert-danger">
                    Failed to load prefix details. HTTP ${response.status}.
                </div>
            `;
            return;
        }

        detailPane.innerHTML = await response.text();
    } catch (err) {
        console.error("Failed to load prefix detail:", err);
        detailPane.innerHTML = `
            <div class="alert alert-danger">
                Failed to load prefix details. Check the browser console for details.
            </div>
        `;
    } finally {
        detailPane.classList.remove("prefix-detail-loading");
    }
}

async function ensurePathExpanded(path, vrfId) {
    /*
     * If multiple VRFs are displayed, the prefix rows may not exist yet.
     * Expand the VRF row first.
     */
    const vrfRow = document.querySelector(
        `tr.tree-row[data-node-type="vrf"][data-vrf-id="${vrfId}"]`
    );

    if (vrfRow && vrfRow.dataset.expanded !== "true") {
        await expand(vrfRow, "", getRowDepth(vrfRow));
    }

    for (const ancestorId of path) {
        const row = document.querySelector(
            `tr.tree-row[data-prefix-id="${ancestorId}"][data-vrf-id="${vrfId}"]`
        );

        if (!row) {
            console.warn(
                "Unable to find ancestor row:",
                ancestorId,
                "vrf:",
                vrfId
            );
            continue;
        }

        const expanded = row.dataset.expanded === "true";

        if (!expanded) {
            await expand(row, row.dataset.prefix, getRowDepth(row));
        }
    }
}

async function searchTree(query) {
    document
        .querySelectorAll(".tree-highlight")
        .forEach(el => {
            el.classList.remove("tree-highlight");
        });

    query = query.trim();

    if (!query) {
        return;
    }

    const url = `/plugins/ipprefix-tree/api/search/?q=${encodeURIComponent(query)}`;

    let response;

    try {
        response = await fetch(url);
    } catch (err) {
        console.error("Search request failed:", err);
        return;
    }

    if (!response.ok) {
        console.error(
            "Search request returned HTTP status:",
            response.status
        );
        return;
    }

    const matches = await response.json();

    for (const match of matches) {
        await ensurePathExpanded(match.path, match.vrf_id);

        const row = document.querySelector(
            `tr.tree-row[data-prefix-id="${match.prefix_id}"][data-vrf-id="${match.vrf_id}"]`
        );

        if (row) {
            row.classList.add("tree-highlight");
            row.scrollIntoView({
                behavior: "smooth",
                block: "center",
            });
        }
    }
}

document.addEventListener(
    "click",
    async function(e) {
        const row = e.target.closest("tr.tree-row");

        if (!row) {
            return;
        }

        const expandIcon = e.target.closest(".tree-expand-icon");

        if (expandIcon && row.dataset.hasChildren === "true") {
            e.preventDefault();
            e.stopPropagation();
            await toggleRowExpansion(row);
            return;
        }

        if (e.target.closest("a") || e.target.closest("button")) {
            return;
        }

        await loadPrefixDetail(row);
    }
);

function bindPrefixSearch() {
    const searchBox = document.getElementById("prefix-search");

    if (!searchBox) {
        console.warn("Prefix search box not found");
        return;
    }

    searchBox.addEventListener(
        "keydown",
        async function(e) {
            if (e.key !== "Enter") {
                return;
            }

            e.preventDefault();
            e.stopPropagation();

            await searchTree(searchBox.value);
        }
    );
}


function setPaneSplit(layout, percent) {
    const safePercent = Math.max(20, Math.min(80, percent));
    layout.style.setProperty("--prefix-tree-left-size", `${safePercent}%`);
    localStorage.setItem("prefixTreeLeftPanePercent", String(safePercent));
}

function bindPaneResizer() {
    const layout = document.querySelector(".prefix-tree-layout");
    const resizer = document.getElementById("prefix-tree-resizer");

    if (!layout || !resizer) {
        return;
    }

    const savedPercent = parseFloat(
        localStorage.getItem("prefixTreeLeftPanePercent") || "33.333"
    );

    if (!Number.isNaN(savedPercent)) {
        setPaneSplit(layout, savedPercent);
    }

    function resizeFromClientX(clientX) {
        const rect = layout.getBoundingClientRect();
        const percent = ((clientX - rect.left) / rect.width) * 100;
        setPaneSplit(layout, percent);
    }

    resizer.addEventListener("pointerdown", function(e) {
        e.preventDefault();
        resizer.setPointerCapture(e.pointerId);
        resizer.classList.add("prefix-tree-resizer-active");
        layout.classList.add("prefix-tree-resizing");
        resizeFromClientX(e.clientX);
    });

    resizer.addEventListener("pointermove", function(e) {
        if (!resizer.hasPointerCapture(e.pointerId)) {
            return;
        }

        resizeFromClientX(e.clientX);
    });

    function stopResize(e) {
        if (resizer.hasPointerCapture(e.pointerId)) {
            resizer.releasePointerCapture(e.pointerId);
        }

        resizer.classList.remove("prefix-tree-resizer-active");
        layout.classList.remove("prefix-tree-resizing");
    }

    resizer.addEventListener("pointerup", stopResize);
    resizer.addEventListener("pointercancel", stopResize);

    resizer.addEventListener("keydown", function(e) {
        const current = parseFloat(
            getComputedStyle(layout).getPropertyValue("--prefix-tree-left-size")
        );
        const step = e.shiftKey ? 10 : 2;

        if (e.key === "ArrowLeft") {
            e.preventDefault();
            setPaneSplit(layout, current - step);
        } else if (e.key === "ArrowRight") {
            e.preventDefault();
            setPaneSplit(layout, current + step);
        } else if (e.key === "Home") {
            e.preventDefault();
            setPaneSplit(layout, 20);
        } else if (e.key === "End") {
            e.preventDefault();
            setPaneSplit(layout, 80);
        } else if (e.key === "0") {
            e.preventDefault();
            setPaneSplit(layout, 33.333);
        }
    });
}

function bindPrefixTreePage() {
    bindPrefixSearch();
    bindPaneResizer();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindPrefixTreePage);
} else {
    bindPrefixTreePage();
}

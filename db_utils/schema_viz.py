"""Cytoscape ER diagram builders for the schema explorer tab."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Tuple

from db_utils.schema_introspect import ColumnInfo, ForeignKeyEdge, SchemaSnapshot

CATEGORY_COLORS: Dict[str, str] = {
    "hub": "#e74c3c",
    "contamination": "#f1c40f",
    "forecast": "#27ae60",
    "meteorology": "#3498db",
    "view": "#9b59b6",
    "system": "#95a5a6",
    "other": "#7f8c8d",
}

CATEGORY_LABELS: Dict[str, str] = {
    "hub": "Stations hub",
    "contamination": "Observations (cont_*)",
    "forecast": "Forecasts",
    "meteorology": "Meteorology (met_*)",
    "view": "Views",
    "system": "PostGIS / system",
    "other": "Other",
}

MAX_LABEL_COLUMNS = 14
POSITION_SCALE = 155
CANVAS_CENTER = (520, 420)

CYTOSCAPE_BASE_STYLESHEET: List[Dict[str, Any]] = [
    {
        "selector": "node",
        "style": {
            "shape": "round-rectangle",
            "width": 260,
            "height": "label",
            "padding": "14px",
            "background-color": "#ffffff",
            "border-width": 2,
            "border-color": "#6c757d",
            "label": "data(label)",
            "text-wrap": "wrap",
            "text-valign": "center",
            "text-halign": "center",
            "font-family": "ui-monospace, SFMono-Regular, Menlo, monospace",
            "font-size": 10,
            "text-margin-y": 4,
            "color": "#212529",
            "overlay-padding": 8,
        },
    },
    {
        "selector": "node.view",
        "style": {
            "border-style": "dashed",
            "background-color": "#faf8ff",
        },
    },
    {
        "selector": "node.hub",
        "style": {"border-color": CATEGORY_COLORS["hub"], "border-width": 3},
    },
    {
        "selector": "node.contamination",
        "style": {"border-color": CATEGORY_COLORS["contamination"]},
    },
    {
        "selector": "node.forecast",
        "style": {"border-color": CATEGORY_COLORS["forecast"]},
    },
    {
        "selector": "node.meteorology",
        "style": {"border-color": CATEGORY_COLORS["meteorology"]},
    },
    {
        "selector": "node.system",
        "style": {"border-color": CATEGORY_COLORS["system"]},
    },
    {
        "selector": "node.other",
        "style": {"border-color": CATEGORY_COLORS["other"]},
    },
    {
        "selector": "edge",
        "style": {
            "curve-style": "taxi",
            "taxi-direction": "horizontal",
            "target-arrow-shape": "triangle",
            "line-style": "solid",
            "line-color": "#495057",
            "target-arrow-color": "#495057",
            "width": 1.5,
            "label": "data(label)",
            "font-size": 9,
            "font-family": "ui-monospace, monospace",
            "text-background-color": "#ffffff",
            "text-background-opacity": 1,
            "text-background-padding": 2,
            "arrow-scale": 0.9,
        },
    },
    {
        "selector": "edge.inferred",
        "style": {
            "line-style": "dashed",
            "line-color": "#adb5bd",
            "target-arrow-color": "#adb5bd",
        },
    },
    {
        "selector": ":selected",
        "style": {
            "border-width": 4,
            "border-color": "#0074D9",
            "line-color": "#0074D9",
            "target-arrow-color": "#0074D9",
            "width": 2.5,
        },
    },
]


def _short_type(data_type: str) -> str:
    """Compact SQL type for node labels."""
    mapping = {
        "character varying": "varchar",
        "character": "char",
        "timestamp without time zone": "timestamp",
        "double precision": "float8",
        "USER-DEFINED": "geometry",
        "real": "float4",
        "integer": "int",
        "bigint": "bigint",
        "smallint": "smallint",
        "text": "text",
    }
    return mapping.get(data_type, data_type)


def filter_object_names(
    snapshot: SchemaSnapshot,
    search: str,
    category: str,
    show_views: bool,
    show_system: bool,
    apply_search: bool = False,
) -> List[str]:
    """
    Filter table/view names shown on the ER diagram.

    Args:
        snapshot: Schema metadata.
        search: Case-insensitive substring (only applied when ``apply_search``).
        category: Category key or ``all``.
        show_views: Include database views.
        show_system: Include PostGIS/system tables.
        apply_search: If True, hide tables/views that do not match ``search``.

    Returns:
        Sorted names matching filters.
    """
    names: List[str] = list(snapshot.tables.keys())
    if show_views:
        names.extend(snapshot.views.keys())

    if not show_system:
        names = [n for n in names if snapshot.category(n) != "system"]

    if category and category != "all":
        names = [n for n in names if snapshot.category(n) == category]

    if apply_search and search:
        needle = search.strip().lower()
        names = [
            n
            for n in names
            if needle in n.lower()
            or _table_matches_column_search(snapshot, n, needle)
        ]

    return sorted(names)


def _table_matches_column_search(
    snapshot: SchemaSnapshot,
    table_name: str,
    needle: str,
) -> bool:
    """True if any column name on the table contains ``needle``."""
    columns = snapshot.tables.get(table_name, snapshot.views.get(table_name, []))
    return any(needle in col.name.lower() for col in columns)


def fk_source_columns(snapshot: SchemaSnapshot, table_name: str) -> Set[str]:
    """Columns on ``table_name`` that reference another table."""
    cols: Set[str] = set()
    for edge in snapshot.edges_for_graph(True):
        if edge.source_table == table_name:
            cols.add(edge.source_column)
    return cols


def _column_role(
    table_name: str,
    column_name: str,
    snapshot: SchemaSnapshot,
) -> str:
    """Return ``pk``, ``fk``, or empty string for label icons."""
    pks = set(snapshot.primary_keys.get(table_name, []))
    if column_name in pks:
        return "pk"
    if column_name in fk_source_columns(snapshot, table_name):
        return "fk"
    return ""


def _column_marker(role: str) -> str:
    """Single-character PK/FK marker for compact labels."""
    if role == "pk":
        return "*"
    if role == "fk":
        return ">"
    return " "


def table_node_label(
    table_name: str,
    columns: List[ColumnInfo],
    snapshot: SchemaSnapshot,
    is_view: bool,
) -> str:
    """
    Multiline Cytoscape node label (table header + columns).

    Cytoscape only supports plain-text labels, so this uses box-drawing
    characters and fixed-width columns to suggest a table layout.

    Args:
        table_name: Object name.
        columns: Ordered columns.
        snapshot: Full schema for PK/FK markers.
        is_view: Whether the object is a view.

    Returns:
        Newline-separated label text.
    """
    kind = "VIEW" if is_view else "TABLE"
    name_width = 22
    type_width = 12
    box_width = name_width + type_width + 3
    title = table_name if len(table_name) <= box_width - 4 else table_name[: box_width - 5] + "…"
    lines = [
        f"┌{'─' * (box_width - 2)}┐",
        f"│ {title:<{box_width - 4}} │",
        f"│ {kind:<{box_width - 4}} │",
        f"├{'─' * name_width}┬{'─' * type_width}┤",
        f"│ {'Column':<{name_width}}│ {'Type':<{type_width}}│",
        f"├{'─' * name_width}┼{'─' * type_width}┤",
    ]
    display_cols = columns
    omitted = 0
    if len(columns) > MAX_LABEL_COLUMNS:
        display_cols = columns[: MAX_LABEL_COLUMNS - 1]
        omitted = len(columns) - len(display_cols)

    for col in display_cols:
        role = _column_role(table_name, col.name, snapshot)
        marker = _column_marker(role)
        typ = _short_type(col.data_type)
        null_suffix = "?" if col.nullable else ""
        col_name = f"{marker} {col.name}"
        if len(col_name) > name_width:
            col_name = col_name[: name_width - 1] + "…"
        type_text = f"{typ}{null_suffix}"
        if len(type_text) > type_width:
            type_text = type_text[: type_width - 1] + "…"
        lines.append(f"│ {col_name:<{name_width}}│ {type_text:<{type_width}}│")

    if omitted:
        note = f"… +{omitted} more column(s)"
        if len(note) > box_width - 4:
            note = note[: box_width - 5] + "…"
        lines.append(f"│ {note:<{box_width - 4}} │")

    lines.append(f"└{'─' * name_width}┴{'─' * type_width}┘")
    return "\n".join(lines)


def table_detail_info(
    snapshot: SchemaSnapshot,
    table_name: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Structured metadata for the schema sidebar table panel.

    Args:
        snapshot: Schema metadata.
        table_name: Selected table or view name.

    Returns:
        Dict with name, kind, category, and column rows; None if not found.
    """
    if not table_name:
        return None

    is_view = table_name in snapshot.views
    columns = snapshot.tables.get(table_name, snapshot.views.get(table_name))
    if columns is None:
        return None

    rows: List[Dict[str, str]] = []
    for col in columns:
        role = _column_role(table_name, col.name, snapshot)
        typ = _short_type(col.data_type)
        rows.append(
            {
                "name": col.name,
                "type": typ,
                "nullable": "yes" if col.nullable else "no",
                "role": role,
                "marker": _column_marker(role).strip() or "—",
            }
        )

    return {
        "name": table_name,
        "kind": "view" if is_view else "table",
        "category": snapshot.category(table_name),
        "columns": rows,
    }


def _preset_positions(
    names: List[str],
    snapshot: SchemaSnapshot,
    edges: List[ForeignKeyEdge],
) -> Dict[str, Dict[str, float]]:
    """Radial preset layout scaled to Cytoscape pixel coordinates."""
    if not names:
        return {}

    hub = "cont_estaciones"
    unit: Dict[str, Tuple[float, float]] = {}

    if hub in names:
        unit[hub] = (0.0, 0.0)

    by_cat: Dict[str, List[str]] = {}
    for name in names:
        if name == hub:
            continue
        cat = snapshot.category(name)
        by_cat.setdefault(cat, []).append(name)

    ring_radii = {
        "contamination": 2.4,
        "forecast": 3.6,
        "meteorology": 4.4,
        "view": 5.2,
        "other": 5.8,
        "system": 6.4,
    }
    angle_offset = {
        "contamination": 0.0,
        "forecast": 0.35,
        "meteorology": 1.0,
        "view": 1.9,
        "other": 2.6,
        "system": 3.3,
    }

    for cat, group in by_cat.items():
        group_sorted = sorted(group)
        n = len(group_sorted)
        radius = ring_radii.get(cat, 5.0)
        offset = angle_offset.get(cat, 0.0)
        for i, name in enumerate(group_sorted):
            angle = offset + (2 * math.pi * i / max(n, 1))
            unit[name] = (radius * math.cos(angle), radius * math.sin(angle))

    missing = [n for n in names if n not in unit]
    for i, name in enumerate(missing):
        angle = math.pi + (math.pi * i / max(len(missing), 1))
        unit[name] = (4.8 * math.cos(angle), 4.8 * math.sin(angle))

    cx, cy = CANVAS_CENTER
    return {
        name: {
            "x": cx + coords[0] * POSITION_SCALE,
            "y": cy + coords[1] * POSITION_SCALE,
        }
        for name, coords in unit.items()
    }


def build_cytoscape_elements(
    snapshot: SchemaSnapshot,
    visible_names: List[str],
    include_inferred: bool,
) -> List[Dict[str, Any]]:
    """
    Build Cytoscape nodes (tables/views) and edges (foreign keys).

    Args:
        snapshot: Schema metadata.
        visible_names: Tables and views to render.
        include_inferred: Include inferred ``id_est`` links.

    Returns:
        List of Cytoscape element dicts.
    """
    visible_set = set(visible_names)
    if not visible_set:
        return []

    edges = [
        e
        for e in snapshot.edges_for_graph(include_inferred)
        if e.source_table in visible_set and e.target_table in visible_set
    ]
    positions = _preset_positions(sorted(visible_set), snapshot, edges)

    elements: List[Dict[str, Any]] = []
    for name in sorted(visible_set):
        is_view = name in snapshot.views
        columns = snapshot.tables.get(name, snapshot.views.get(name, []))
        category = snapshot.category(name)
        label = table_node_label(name, columns, snapshot, is_view)
        classes = ["table", category]
        if is_view:
            classes.append("view")

        node: Dict[str, Any] = {
            "data": {
                "id": name,
                "label": label,
                "kind": "view" if is_view else "table",
                "category": category,
            },
            "classes": " ".join(classes),
        }
        if name in positions:
            node["position"] = positions[name]
        elements.append(node)

    seen_edge_ids: Set[str] = set()
    for edge in edges:
        edge_id = (
            f"{edge.source_table}__{edge.source_column}__"
            f"{edge.target_table}__{edge.constraint_name}"
        )
        if edge_id in seen_edge_ids:
            continue
        seen_edge_ids.add(edge_id)
        inferred = edge.constraint_name.startswith("inferred")
        elements.append(
            {
                "data": {
                    "id": edge_id,
                    "source": edge.source_table,
                    "target": edge.target_table,
                    "label": edge.source_column,
                    "target_column": edge.target_column,
                    "inferred": inferred,
                },
                "classes": "inferred" if inferred else "fk",
            }
        )

    return elements


def build_cytoscape_stylesheet(
    search: Optional[str],
    selected_node: Optional[str],
    snapshot: SchemaSnapshot,
    visible_names: List[str],
    include_inferred: bool,
) -> List[Dict[str, Any]]:
    """
    Base stylesheet plus dynamic search / selection / neighborhood rules.

    Args:
        search: Search string for highlighting matching nodes.
        selected_node: Table or view id from ``tapNodeData``.
        snapshot: Schema metadata.
        visible_names: Currently visible object names.
        include_inferred: Whether inferred edges are shown.

    Returns:
        Full Cytoscape stylesheet list.
    """
    sheet = list(CYTOSCAPE_BASE_STYLESHEET)
    visible_set = set(visible_names)
    if not visible_set:
        return sheet

    needle = (search or "").strip().lower()
    if needle:
        for name in visible_names:
            columns = snapshot.tables.get(name, snapshot.views.get(name, []))
            hit = (
                needle in name.lower()
                or any(needle in col.name.lower() for col in columns)
            )
            if hit:
                sheet.append(
                    {
                        "selector": f'node[id = "{name}"]',
                        "style": {
                            "border-width": 4,
                            "border-color": "#ff4136",
                            "background-color": "#fff5f5",
                        },
                    }
                )

    if selected_node and selected_node in visible_set:
        neighbors, incident = snapshot.related_tables(selected_node, include_inferred)
        sheet.append(
            {
                "selector": f'node[id = "{selected_node}"]',
                "style": {
                    "border-width": 4,
                    "border-color": "#0074D9",
                    "background-color": "#eef6fc",
                },
            }
        )
        for neighbor in neighbors:
            if neighbor in visible_set:
                sheet.append(
                    {
                        "selector": f'node[id = "{neighbor}"]',
                        "style": {
                            "border-width": 3,
                            "border-color": "#6c5ce7",
                            "background-color": "#f8f7ff",
                        },
                    }
                )
        for edge in incident:
            if edge.source_table in visible_set and edge.target_table in visible_set:
                edge_id = (
                    f"{edge.source_table}__{edge.source_column}__"
                    f"{edge.target_table}__{edge.constraint_name}"
                )
                sheet.append(
                    {
                        "selector": f'edge[id = "{edge_id}"]',
                        "style": {
                            "line-color": "#6c5ce7",
                            "target-arrow-color": "#6c5ce7",
                            "width": 2.5,
                        },
                    }
                )

        dim_nodes = visible_set - {selected_node} - set(neighbors)
        for name in dim_nodes:
            sheet.append(
                {
                    "selector": f'node[id = "{name}"]',
                    "style": {"opacity": 0.2},
                }
            )

    return sheet


def format_tap_node_detail(node_data: Optional[Dict[str, Any]]) -> str:
    """Legacy plain-text detail (kept for tests); prefer ``table_detail_info`` in UI."""
    if not node_data:
        return "Click a table or view in the diagram.\n\nPan: drag background · Zoom: scroll"
    return str(node_data.get("label", node_data.get("id", "")))


def format_tap_edge_detail(edge_data: Optional[Dict[str, Any]]) -> str:
    """Format sidebar text for a tapped foreign-key edge."""
    if not edge_data:
        return ""
    inferred = edge_data.get("inferred")
    tag = " (inferred)" if inferred else ""
    return (
        f"Foreign key{tag}\n"
        f"{edge_data.get('source')}.{edge_data.get('label')} "
        f"→ {edge_data.get('target')}.{edge_data.get('target_column', 'id')}"
    )


def build_relationship_summary(
    snapshot: SchemaSnapshot,
    table_name: Optional[str],
    include_inferred: bool,
) -> List[str]:
    """
    Short FK summary lines for the sidebar.

    Args:
        snapshot: Schema metadata.
        table_name: Selected table, if any.
        include_inferred: Include inferred links.

    Returns:
        Lines of plain text for display.
    """
    if not table_name:
        return []

    _, edges = snapshot.related_tables(table_name, include_inferred)
    lines: List[str] = []
    for edge in edges:
        inferred = " [inferred]" if edge.constraint_name.startswith("inferred") else ""
        if edge.source_table == table_name:
            lines.append(
                f"→ {edge.target_table}.{edge.target_column} "
                f"({edge.source_column}){inferred}"
            )
        else:
            lines.append(
                f"← {edge.source_table}.{edge.source_column} "
                f"({edge.target_column}){inferred}"
            )
    return lines

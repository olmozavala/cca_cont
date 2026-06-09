"""Load PostgreSQL schema metadata for the interactive dashboard explorer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from db_utils.sql_con import get_db_engine

SCHEMA_NAME = "public"

TABLES_SQL = """
    SELECT table_name, column_name, data_type, is_nullable, ordinal_position
    FROM information_schema.columns
    WHERE table_schema = :schema
      AND table_name IN (
          SELECT table_name FROM information_schema.tables
          WHERE table_schema = :schema AND table_type = 'BASE TABLE'
      )
    ORDER BY table_name, ordinal_position
"""

VIEWS_SQL = """
    SELECT table_name, column_name, data_type, is_nullable, ordinal_position
    FROM information_schema.columns
    WHERE table_schema = :schema
      AND table_name IN (
          SELECT table_name FROM information_schema.views
          WHERE table_schema = :schema
      )
    ORDER BY table_name, ordinal_position
"""

PRIMARY_KEYS_SQL = """
    SELECT tc.table_name, kcu.column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type = 'PRIMARY KEY'
      AND tc.table_schema = :schema
    ORDER BY tc.table_name, kcu.ordinal_position
"""

FOREIGN_KEYS_SQL = """
    SELECT
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name,
        tc.constraint_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema = :schema
    ORDER BY tc.table_name, kcu.column_name
"""


@dataclass
class ColumnInfo:
    """One column on a table or view."""

    name: str
    data_type: str
    nullable: bool


@dataclass
class ForeignKeyEdge:
    """Directed FK: source table.column → target table.column."""

    source_table: str
    source_column: str
    target_table: str
    target_column: str
    constraint_name: str


@dataclass
class SchemaSnapshot:
    """Full schema graph used by the dashboard."""

    tables: Dict[str, List[ColumnInfo]] = field(default_factory=dict)
    views: Dict[str, List[ColumnInfo]] = field(default_factory=dict)
    foreign_keys: List[ForeignKeyEdge] = field(default_factory=list)
    inferred_links: List[ForeignKeyEdge] = field(default_factory=list)
    primary_keys: Dict[str, List[str]] = field(default_factory=dict)

    def all_object_names(self) -> List[str]:
        """Sorted table and view names."""
        return sorted(set(self.tables) | set(self.views))

    def category(self, name: str) -> str:
        """Group name for styling (cont, forecast, met, view, system, other)."""
        if name in self.views:
            return "view"
        if name == "cont_estaciones":
            return "hub"
        if name.startswith("cont_"):
            return "contamination"
        if name.startswith("forecast_"):
            return "forecast"
        if name.startswith("met_"):
            return "meteorology"
        if name in {"spatial_ref_sys", "geometry_columns", "geography_columns"}:
            return "system"
        return "other"

    def edges_for_graph(self, include_inferred: bool = True) -> List[ForeignKeyEdge]:
        """All relationship edges to draw."""
        edges = list(self.foreign_keys)
        if include_inferred:
            edges.extend(self.inferred_links)
        return edges

    def related_tables(self, table_name: str, include_inferred: bool = True) -> Tuple[List[str], List[ForeignKeyEdge]]:
        """
        Tables linked to ``table_name`` and the edges touching it.

        Returns:
            Tuple of (neighbor table names, incident edges).
        """
        neighbors: set[str] = set()
        incident: List[ForeignKeyEdge] = []
        for edge in self.edges_for_graph(include_inferred):
            if edge.source_table == table_name:
                neighbors.add(edge.target_table)
                incident.append(edge)
            elif edge.target_table == table_name:
                neighbors.add(edge.source_table)
                incident.append(edge)
        return sorted(neighbors), incident


def _rows_to_columns(df: pd.DataFrame) -> Dict[str, List[ColumnInfo]]:
    """Build table/view name → columns mapping from information_schema rows."""
    result: Dict[str, List[ColumnInfo]] = {}
    if df.empty:
        return result
    for table_name, group in df.groupby("table_name", sort=False):
        cols: List[ColumnInfo] = []
        for _, row in group.sort_values("ordinal_position").iterrows():
            cols.append(
                ColumnInfo(
                    name=str(row["column_name"]),
                    data_type=str(row["data_type"]),
                    nullable=str(row["is_nullable"]).upper() == "YES",
                )
            )
        result[str(table_name)] = cols
    return result


def _infer_id_est_links(tables: Dict[str, List[ColumnInfo]]) -> List[ForeignKeyEdge]:
    """Link tables with ``id_est`` to ``cont_estaciones`` when no formal FK exists."""
    hub = "cont_estaciones"
    if hub not in tables:
        return []
    inferred: List[ForeignKeyEdge] = []
    for table_name, columns in tables.items():
        if table_name == hub:
            continue
        if any(col.name == "id_est" for col in columns):
            inferred.append(
                ForeignKeyEdge(
                    source_table=table_name,
                    source_column="id_est",
                    target_table=hub,
                    target_column="id",
                    constraint_name="inferred_id_est",
                )
            )
    return inferred


def load_schema_snapshot(engine: Optional[Engine] = None) -> SchemaSnapshot:
    """
    Query live PostgreSQL metadata for tables, views, and foreign keys.

    Args:
        engine: SQLAlchemy engine; uses ``get_db_engine()`` when omitted.

    Returns:
        SchemaSnapshot for the public schema.
    """
    db_engine = engine or get_db_engine()
    if db_engine is None:
        return SchemaSnapshot()

    params = {"schema": SCHEMA_NAME}
    with db_engine.connect() as conn:
        tables_df = pd.read_sql(text(TABLES_SQL), conn, params=params)
        views_df = pd.read_sql(text(VIEWS_SQL), conn, params=params)
        fk_df = pd.read_sql(text(FOREIGN_KEYS_SQL), conn, params=params)
        pk_df = pd.read_sql(text(PRIMARY_KEYS_SQL), conn, params=params)

    tables = _rows_to_columns(tables_df)
    views = _rows_to_columns(views_df)
    foreign_keys: List[ForeignKeyEdge] = []
    if not fk_df.empty:
        for _, row in fk_df.iterrows():
            foreign_keys.append(
                ForeignKeyEdge(
                    source_table=str(row["table_name"]),
                    source_column=str(row["column_name"]),
                    target_table=str(row["foreign_table_name"]),
                    target_column=str(row["foreign_column_name"]),
                    constraint_name=str(row["constraint_name"]),
                )
            )

    inferred = _infer_id_est_links(tables)
    fk_pairs = {
        (e.source_table, e.source_column, e.target_table, e.target_column)
        for e in foreign_keys
    }
    inferred = [
        edge
        for edge in inferred
        if (edge.source_table, edge.source_column, edge.target_table, edge.target_column)
        not in fk_pairs
    ]

    primary_keys: Dict[str, List[str]] = {}
    if not pk_df.empty:
        for table_name, group in pk_df.groupby("table_name", sort=False):
            primary_keys[str(table_name)] = [str(c) for c in group["column_name"].tolist()]

    return SchemaSnapshot(
        tables=tables,
        views=views,
        foreign_keys=foreign_keys,
        inferred_links=inferred,
        primary_keys=primary_keys,
    )


def snapshot_to_store_dict(snapshot: SchemaSnapshot) -> Dict[str, object]:
    """Serialize snapshot for ``dcc.Store`` (JSON-friendly)."""
    return {
        "tables": {
            name: [{"name": c.name, "data_type": c.data_type, "nullable": c.nullable} for c in cols]
            for name, cols in snapshot.tables.items()
        },
        "views": {
            name: [{"name": c.name, "data_type": c.data_type, "nullable": c.nullable} for c in cols]
            for name, cols in snapshot.views.items()
        },
        "foreign_keys": [
            {
                "source_table": e.source_table,
                "source_column": e.source_column,
                "target_table": e.target_table,
                "target_column": e.target_column,
                "constraint_name": e.constraint_name,
            }
            for e in snapshot.foreign_keys
        ],
        "inferred_links": [
            {
                "source_table": e.source_table,
                "source_column": e.source_column,
                "target_table": e.target_table,
                "target_column": e.target_column,
                "constraint_name": e.constraint_name,
            }
            for e in snapshot.inferred_links
        ],
        "primary_keys": snapshot.primary_keys,
    }


def snapshot_from_store_dict(data: Optional[Dict[str, object]]) -> SchemaSnapshot:
    """Rebuild SchemaSnapshot from ``dcc.Store`` data."""
    if not data:
        return SchemaSnapshot()

    def _cols(block: Dict[str, List[Dict[str, object]]]) -> Dict[str, List[ColumnInfo]]:
        out: Dict[str, List[ColumnInfo]] = {}
        for name, col_list in block.items():
            out[name] = [
                ColumnInfo(
                    name=str(c["name"]),
                    data_type=str(c["data_type"]),
                    nullable=bool(c["nullable"]),
                )
                for c in col_list
            ]
        return out

    def _edges(key: str) -> List[ForeignKeyEdge]:
        raw = data.get(key) or []
        return [
            ForeignKeyEdge(
                source_table=str(e["source_table"]),
                source_column=str(e["source_column"]),
                target_table=str(e["target_table"]),
                target_column=str(e["target_column"]),
                constraint_name=str(e["constraint_name"]),
            )
            for e in raw
        ]

    pk_raw = data.get("primary_keys") or {}
    primary_keys = {str(t): [str(c) for c in cols] for t, cols in pk_raw.items()}

    return SchemaSnapshot(
        tables=_cols(data.get("tables") or {}),
        views=_cols(data.get("views") or {}),
        foreign_keys=_edges("foreign_keys"),
        inferred_links=_edges("inferred_links"),
        primary_keys=primary_keys,
    )

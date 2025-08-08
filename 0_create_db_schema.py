import psycopg2
import netrc
from typing import List, Tuple, Dict
from db_utils.sql_common import get_db_connection

SCHEMA = 'public'
OUTPUT_MD = 'schema.md'


def get_tables_and_columns(conn) -> Dict[str, List[Tuple[str, str]]]:
    """
    Retrieve all tables and their columns with types from the database.

    Args:
        conn: psycopg2 connection object.

    Returns:
        Dict[str, List[Tuple[str, str]]]: Mapping of table name to list of (column name, data type).
    """
    query = f'''
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s
        AND table_name IN (
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
        )
        ORDER BY table_name, ordinal_position;
    '''
    with conn.cursor() as cur:
        cur.execute(query, (SCHEMA, SCHEMA))
        rows = cur.fetchall()
    tables: Dict[str, List[Tuple[str, str]]] = {}
    for table_name, column_name, data_type in rows:
        tables.setdefault(table_name, []).append((column_name, data_type))
    return tables


def get_foreign_keys(conn) -> Dict[str, List[Tuple[str, str, str, str]]]:
    """
    Retrieve all foreign key relationships for tables in the schema.

    Args:
        conn: psycopg2 connection object.

    Returns:
        Dict[str, List[Tuple[str, str, str, str]]]: Mapping of table name to a list of (column, referenced_table, referenced_column, constraint_name).
    """
    query = f'''
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
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = %s
        ORDER BY tc.table_name, kcu.column_name;
    '''
    with conn.cursor() as cur:
        cur.execute(query, (SCHEMA,))
        rows = cur.fetchall()
    fks: Dict[str, List[Tuple[str, str, str, str]]] = {}
    for table, column, ref_table, ref_column, constraint_name in rows:
        fks.setdefault(table, []).append((column, ref_table, ref_column, constraint_name))
    return fks


def get_views_and_columns(conn) -> Dict[str, List[Tuple[str, str]]]:
    """
    Retrieve all views and their columns with types from the database.

    Args:
        conn: psycopg2 connection object.

    Returns:
        Dict[str, List[Tuple[str, str]]]: Mapping of view name to list of (column name, data type).
    """
    query = f'''
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s
        AND table_name IN (
            SELECT table_name FROM information_schema.views
            WHERE table_schema = %s
        )
        ORDER BY table_name, ordinal_position;
    '''
    with conn.cursor() as cur:
        cur.execute(query, (SCHEMA, SCHEMA))
        rows = cur.fetchall()
    views: Dict[str, List[Tuple[str, str]]] = {}
    for view_name, column_name, data_type in rows:
        views.setdefault(view_name, []).append((column_name, data_type))
    return views


def write_schema_markdown(
    tables: Dict[str, List[Tuple[str, str]]],
    foreign_keys: Dict[str, List[Tuple[str, str, str, str]]],
    views: Dict[str, List[Tuple[str, str]]],
    output_file: str
) -> None:
    """
    Write the tables, foreign keys, and views schema information to a Markdown file.

    Args:
        tables: Mapping of table name to list of (column name, data type).
        foreign_keys: Mapping of table name to list of (column, referenced_table, referenced_column, constraint_name).
        views: Mapping of view name to list of (column name, data type).
        output_file: Path to the output Markdown file.
    """
    with open(output_file, 'w') as f:
        f.write('# Database Schema\n\n')
        f.write('## Tables\n\n')
        for table, columns in tables.items():
            f.write(f'### {table}\n')
            f.write('| Column | Type |\n|--------|------|\n')
            for col, dtype in columns:
                f.write(f'| {col} | {dtype} |\n')
            f.write('\n')
            # Foreign keys section
            fks = foreign_keys.get(table, [])
            if fks:
                f.write('**Foreign Keys:**\n\n')
                f.write('| Column | References |\n|--------|------------|\n')
                for col, ref_table, ref_col, constraint_name in fks:
                    f.write(f'| {col} | {ref_table}({ref_col}) |\n')
                f.write('\n')
        f.write('## Views\n\n')
        for view, columns in views.items():
            f.write(f'### {view}\n')
            f.write('| Column | Type |\n|--------|------|\n')
            for col, dtype in columns:
                f.write(f'| {col} | {dtype} |\n')
            f.write('\n')


def main() -> None:
    """
    Main function to extract schema and write to Markdown file.
    """
    conn = get_db_connection()
    try:
        tables = get_tables_and_columns(conn)
        foreign_keys = get_foreign_keys(conn)
        views = get_views_and_columns(conn)
        write_schema_markdown(tables, foreign_keys, views, OUTPUT_MD)
        print(f"Schema written to {OUTPUT_MD}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()


def test_get_tables_and_columns(monkeypatch) -> None:
    """
    Pytest function to test get_tables_and_columns with a mock connection.
    """
    # This is a placeholder for a pytest function. You should implement a mock connection and cursor.
    pass

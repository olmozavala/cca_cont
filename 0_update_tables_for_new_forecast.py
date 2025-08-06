#!/usr/bin/env python3
"""
Script to add new hour columns to forecast tables for enhanced forecasting capabilities.
This script adds min_hour_p01, max_hour_p01, avg_hour_p01 through min_hour_p24, max_hour_p24, avg_hour_p24
to all forecast tables except forecast_otres (which already has these columns).
"""

import sys
from typing import List, Tuple
from sqlalchemy import text

# Add the db_utils directory to the path
sys.path.insert(0, './db_utils')

from db_utils.sql_con import get_db_engine


def get_forecast_tables() -> List[str]:
    """
    Get all forecast table names except forecast_otres.
    
    Returns:
        List[str]: List of forecast table names to update
    """
    return [
        'forecast_co',
        'forecast_no', 
        'forecast_nodos',
        'forecast_nox',
        'forecast_pmco',
        'forecast_pmdiez',
        'forecast_pmdoscinco',
        'forecast_sodos'
    ]


def get_hour_columns() -> List[str]:
    """
    Generate the list of hour columns to add (p01 through p24).
    
    Returns:
        List[str]: List of column names to add
    """
    columns = []
    for i in range(1, 25):
        hour_num = f"{i:02d}"
        columns.extend([
            f"min_hour_p{hour_num}",
            f"max_hour_p{hour_num}", 
            f"avg_hour_p{hour_num}"
        ])
    return columns


def check_table_exists(engine, table_name: str) -> bool:
    """
    Check if a table exists in the database.
    
    Args:
        engine: SQLAlchemy engine
        table_name (str): Name of the table to check
        
    Returns:
        bool: True if table exists, False otherwise
    """
    try:
        with engine.connect() as connection:
            check_sql = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = :table_name
                )
            """)
            result = connection.execute(check_sql, {'table_name': table_name})
            return result.fetchone()[0]
    except Exception as e:
        print(f"Error checking if table {table_name} exists: {e}")
        return False


def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    """
    Check if a column exists in a table.
    
    Args:
        engine: SQLAlchemy engine
        table_name (str): Name of the table
        column_name (str): Name of the column to check
        
    Returns:
        bool: True if column exists, False otherwise
    """
    try:
        with engine.connect() as connection:
            check_sql = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = :table_name AND column_name = :column_name
                )
            """)
            result = connection.execute(check_sql, {
                'table_name': table_name,
                'column_name': column_name
            })
            return result.fetchone()[0]
    except Exception as e:
        print(f"Error checking if column {column_name} exists in table {table_name}: {e}")
        return False


def add_columns_to_table(engine, table_name: str, columns: List[str]) -> Tuple[bool, str]:
    """
    Add columns to a table.
    
    Args:
        engine: SQLAlchemy engine
        table_name (str): Name of the table to modify
        columns (List[str]): List of column names to add
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        with engine.connect() as connection:
            # Start a transaction
            with connection.begin():
                for column in columns:
                    if not check_column_exists(engine, table_name, column):
                        add_column_sql = text(f"""
                            ALTER TABLE {table_name} 
                            ADD COLUMN {column} REAL
                        """)
                        connection.execute(add_column_sql)
                        print(f"Added column {column} to table {table_name}")
                    else:
                        print(f"Column {column} already exists in table {table_name}")
                
                # Commit the transaction
                connection.commit()
                return True, f"Successfully added columns to table {table_name}"
                
    except Exception as e:
        return False, f"Error adding columns to table {table_name}: {e}"


def update_table_schema(engine, table_name: str) -> Tuple[bool, str]:
    """
    Update a single table's schema by adding the new hour columns.
    
    Args:
        engine: SQLAlchemy engine
        table_name (str): Name of the table to update
        
    Returns:
        Tuple[bool, str]: (success, message)
    """
    print(f"\nProcessing table: {table_name}")
    
    # Check if table exists
    if not check_table_exists(engine, table_name):
        return False, f"Table {table_name} does not exist"
    
    # Get the columns to add
    columns_to_add = get_hour_columns()
    
    # Add columns to the table
    success, message = add_columns_to_table(engine, table_name, columns_to_add)
    
    if success:
        print(f"✓ Successfully updated table {table_name}")
    else:
        print(f"✗ Failed to update table {table_name}: {message}")
    
    return success, message


def main() -> None:
    """
    Main function to update all forecast tables with new hour columns.
    """
    print("Starting forecast table schema update...")
    
    # Get database engine
    engine = get_db_engine()
    if not engine:
        print("Failed to connect to database")
        return
    
    # Get list of tables to update
    tables_to_update = get_forecast_tables()
    print(f"Tables to update: {', '.join(tables_to_update)}")
    
    # Track results
    successful_updates = []
    failed_updates = []
    
    # Update each table
    for table_name in tables_to_update:
        success, message = update_table_schema(engine, table_name)
        if success:
            successful_updates.append(table_name)
        else:
            failed_updates.append((table_name, message))
    
    # Print summary
    print("\n" + "="*50)
    print("UPDATE SUMMARY")
    print("="*50)
    print(f"Successfully updated {len(successful_updates)} tables:")
    for table in successful_updates:
        print(f"  ✓ {table}")
    
    if failed_updates:
        print(f"\nFailed to update {len(failed_updates)} tables:")
        for table, message in failed_updates:
            print(f"  ✗ {table}: {message}")
    else:
        print("\nAll tables updated successfully!")
    
    print(f"\nTotal tables processed: {len(tables_to_update)}")
    print("Schema update complete.")


if __name__ == '__main__':
    main()


def test_get_forecast_tables() -> None:
    """
    Pytest function to test get_forecast_tables function.
    """
    tables = get_forecast_tables()
    assert 'forecast_co' in tables
    assert 'forecast_otres' not in tables
    assert len(tables) == 8


def test_get_hour_columns() -> None:
    """
    Pytest function to test get_hour_columns function.
    """
    columns = get_hour_columns()
    assert 'min_hour_p01' in columns
    assert 'max_hour_p01' in columns
    assert 'avg_hour_p01' in columns
    assert 'min_hour_p24' in columns
    assert 'max_hour_p24' in columns
    assert 'avg_hour_p24' in columns
    assert len(columns) == 72  # 24 hours * 3 columns per hour

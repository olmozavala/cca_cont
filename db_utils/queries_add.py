from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import text
from .sql_con import get_db_engine
from db_utils.oztools import ContIOTools


def _is_valid_table(table: str) -> bool:
    """
    Check if the table name is valid (from the known list).
    """
    valid_tables = set(ContIOTools().getTables() + ContIOTools().getMeteoTables())
    return table in valid_tables


def insert_pollutant_data(table: str, fecha: str, id_est: str, value: str) -> bool:
    """
    Insert a single pollutant measurement into the specified table.
    
    Args:
        table (str): The table name (e.g., 'cont_o3', 'cont_pm10')
        fecha (str): Date string in format 'MM/DD/YYYY HH:MM:SS'
        id_est (str): Station ID
        value (str): Measurement value
        
    Returns:
        bool: True if insertion successful, False otherwise
    """
    if not _is_valid_table(table):
        print(f"❌ Invalid table name: {table}")
        return False
    engine = get_db_engine()
    if engine is None:
        print("❌ Failed to create database engine")
        return False
    
    try:
        date_format = "MM/DD/YYYY/HH24"
        # Directly interpolate the table name (safe because it's from your own list)
        sql = text(f"""
            SET TimeZone='UTC';
            INSERT INTO {table} (fecha, val, id_est)
            VALUES (to_timestamp(:fecha, :date_format), :value, :id_est)
        """)
        with engine.connect() as connection:
            connection.execute(sql, {
                'fecha': fecha,
                'date_format': date_format,
                'value': value,
                'id_est': id_est
            })
            connection.commit()
        return True
    except Exception as e:
        if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
            print(f"Row already existed in {table} for {fecha} {id_est}")
        else:
            print(f"❌ Error inserting data into {table}: {e}")
        return False


def insert_meteorological_data(table: str, fecha: str, id_est: str, value: str) -> bool:
    """
    Insert a single meteorological measurement into the specified table.
    
    Args:
        table (str): The table name (e.g., 'met_tmp', 'met_rh')
        fecha (str): Date string in format 'MM/DD/YYYY HH:MM:SS'
        id_est (str): Station ID
        value (str): Measurement value
        
    Returns:
        bool: True if insertion successful, False otherwise
    """
    return insert_pollutant_data(table, fecha, id_est, value)


def batch_insert_data(data_records: list) -> Dict[str, int]:
    """
    Insert multiple data records in batch for better performance.
    
    Args:
        data_records (list): List of dictionaries with keys: table, fecha, id_est, value
        
    Returns:
        Dict[str, int]: Statistics of insertions {'success': count, 'failed': count}
    """
    engine = get_db_engine()
    if engine is None:
        print("❌ Failed to create database engine")
        return {'success': 0, 'failed': len(data_records)}
    
    success_count = 0
    failed_count = 0
    
    try:
        with engine.connect() as connection:
            for record in data_records:
                try:
                    table = record['table']
                    if not _is_valid_table(table):
                        print(f"❌ Invalid table name: {table}")
                        failed_count += 1
                        continue
                    sql = text(f"""
                        SET TimeZone='UTC';
                        INSERT INTO {table} (fecha, val, id_est)
                        VALUES (to_timestamp(:fecha, 'MM/DD/YYYY/HH24'), :value, :id_est)
                    """)
                    connection.execute(sql, {
                        'fecha': record['fecha'],
                        'value': record['value'],
                        'id_est': record['id_est']
                    })
                    success_count += 1
                except Exception as e:
                    if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
                        # Row already exists, not counting as failure
                        pass
                    else:
                        print(f"❌ Error inserting record: {e}")
                        failed_count += 1
            connection.commit()
    except Exception as e:
        print(f"❌ Batch insert error: {e}")
        failed_count += len(data_records)
    return {'success': success_count, 'failed': failed_count}

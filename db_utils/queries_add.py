import logging
import os
from typing import Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy import text, Connection
from .sql_con import get_db_engine
from db_utils.oztools import ContIOTools

# Set up logging configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def _is_valid_table(table: str) -> bool:
    """
    Check if the table name is valid (from the known list).
    """
    valid_tables = set(ContIOTools().getTables() + ContIOTools().getMeteoTables())
    return table in valid_tables


def insert_data(table: str, fecha: str, id_est: str, value: str, connection: Optional[Connection] = None) -> Union[bool, str]:
    """
    Insert a single pollutant measurement into the specified table.
    
    Args:
        table (str): The table name (e.g., 'cont_o3', 'cont_pm10')
        fecha (str): Date string in format 'MM/DD/YYYY HH24:MI:SS'
        id_est (str): Station ID
        value (str): Measurement value
        connection (Optional[Connection]): SQLAlchemy connection to use. If None, a new connection is opened.
        
    Returns:
        bool: True if insertion successful, False otherwise
        str: 'duplicate' if row already existed
    """

    if not _is_valid_table(table):
        logging.error(f"Invalid table name: {table}")
        return False

    date_format = "MM/DD/YYYY HH24:MI:SS"

    sql = text(f"""
        SET TimeZone='UTC';
        INSERT INTO {table} (fecha, val, id_est)
        VALUES (to_timestamp(:fecha, :date_format), :value, :id_est)
    """)

    try:
        if connection is not None:
            connection.execute(sql, {
                'fecha': fecha,
                'date_format': date_format,
                'value': value,
                'id_est': id_est
            })
            return True
        else:
            engine = get_db_engine()
            with engine.connect() as conn:
                conn.execute(sql, {
                    'fecha': fecha,
                    'date_format': date_format,
                    'value': value,
                    'id_est': id_est
                })
                conn.commit()
            return True
    except Exception as e:
        if connection is not None:
            try:
                connection.rollback()
            except Exception as rb_e:
                logging.error(f"Rollback failed: {rb_e}")
        if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
            logging.info(f"Row already existed in {table} for {fecha} {id_est}")
            return 'duplicate'
        else:
            logging.error(f"Error inserting data into {table}: {e}")
        return False

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
        logging.error("Failed to create database engine")
        return {'success': 0, 'failed': len(data_records)}
    
    success_count = 0
    failed_count = 0
    
    try:
        with engine.connect() as connection:
            for record in data_records:
                try:
                    table = record['table']
                    if not _is_valid_table(table):
                        logging.error(f"Invalid table name: {table}")
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
                    if connection is not None:
                        try:
                            connection.rollback()
                        except Exception as rb_e:
                            logging.error(f"Rollback failed: {rb_e}")
                    if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
                        logging.info(f"Row already existed in {table} for {record['fecha']} {record['id_est']}")
                        # Row already exists, not counting as failure
                        pass
                    else:
                        logging.error(f"Error inserting record: {e}")
                        failed_count += 1
            connection.commit()
    except Exception as e:
        logging.error(f"Batch insert error: {e}")
        failed_count += len(data_records)
    return {'success': success_count, 'failed': failed_count}

#!/usr/bin/env python3
"""
Script to update pollutant and meteorological data by month.
This script fetches data from the Mexico City air quality API and inserts it into the database.
"""

import sys
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import argparse
import logging
import warnings
from sqlalchemy import text

# Add the db_utils directory to the path
sys.path.insert(0, './db_utils')

from db_utils.oztools import ContIOTools
from db_utils.sql_con import get_db_engine, clean_data_value
from db_utils.html_reader import read_html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Suppress BeautifulSoup encoding warnings
warnings.filterwarnings("ignore", message="You provided Unicode markup but also provided a value for from_encoding")


def prepare_bulk_data(data: pd.DataFrame, table: str, stations: List[str]) -> List[Dict[str, Any]]:
    """
    Prepare data for bulk insert operation.
    
    Args:
        data (pd.DataFrame): Raw data from API
        table (str): Target table name
        stations (List[str]): List of station names
        
    Returns:
        List[Dict[str, Any]]: List of records ready for bulk insert
    """
    bulk_records = []
    
    for row_id in range(len(data)):
        row = data.iloc[row_id]
        fecha_split = row.iloc[0].split('-')
        
        # Parse date
        try:
            row_day = int(fecha_split[0])
            row_month = int(fecha_split[1])
            row_year = int(fecha_split[2])
        except Exception:
            logger.warning(f"Invalid date format: {row.iloc[0]}, skipping row {row_id}")
            continue
        
        # Parse hour
        time_value = str(row.iloc[1])
        try:
            hour = int(time_value)
            time_str = f"{hour-1:02d}:00:00"
        except Exception:
            logger.warning(f"Invalid time value: {time_value}, skipping row {row_id}")
            continue
        
        fecha = f"{row_month:02d}/{row_day:02d}/{row_year} {time_str}"
        
        # Process each station (column)
        for col_id in range(2, len(row)):
            value = row.iloc[col_id]
            value_clean = clean_data_value(value)
            
            if value_clean != 'nr':
                if isinstance(value, (np.integer, np.floating)):
                    value_native = value.item()
                else:
                    value_native = value_clean
                
                bulk_records.append({
                    'table': table,
                    'fecha': fecha,
                    'id_est': str(stations[col_id]),
                    'value': str(value_native)
                })
    
    return bulk_records


def bulk_insert_records(records: List[Dict[str, Any]], engine) -> Dict[str, int]:
    """
    Perform bulk insert operation using SQLAlchemy.
    
    Args:
        records (List[Dict[str, Any]]): List of records to insert
        engine: SQLAlchemy engine
        
    Returns:
        Dict[str, int]: Statistics of insertions {'success': count, 'failed': count, 'duplicate': count}
    """
    if not records:
        return {'success': 0, 'failed': 0, 'duplicate': 0}
    
    # Group records by table for efficient bulk insert
    table_groups = {}
    for record in records:
        table = record['table']
        if table not in table_groups:
            table_groups[table] = []
        table_groups[table].append(record)
    
    success_count = 0
    failed_count = 0
    duplicate_count = 0
    
    with engine.begin() as connection:  # Automatically commits
        for table, table_records in table_groups.items():
            try:
                # Create insert statement for this table
                stmt = text(f"""
                    INSERT INTO {table} (fecha, val, id_est)
                    VALUES (to_timestamp(:fecha, 'MM/DD/YYYY HH24:MI:SS'), :value, :id_est)
                """)
                
                # Prepare data for bulk insert
                insert_data = [
                    {
                        'fecha': record['fecha'],
                        'value': record['value'],
                        'id_est': record['id_est']
                    }
                    for record in table_records
                ]
                
                # Execute bulk insert
                result = connection.execute(stmt, insert_data)
                success_count += result.rowcount
                logger.info(f"Successfully inserted {result.rowcount} records into {table}")
                
            except Exception as e:
                logger.error(f"Error in bulk insert for table {table}: {e}")
                failed_count += len(table_records)
    
    return {
        'success': success_count,
        'failed': failed_count,
        'duplicate': duplicate_count
    }


def update_tables_by_month(oz_tools: ContIOTools, tables: List[str], parameters: List[str], 
                          month: int, year: int, requested_month: int, requested_year: int) -> None:
    """
    Update tables with data for a specific month using bulk insert operations.
    
    Args:
        oz_tools (ContIOTools): Helper object for table and parameter mappings
        tables (List[str]): List of table names to update
        parameters (List[str]): List of parameter names for API calls
        month (int): Month to update (1-12)
        year (int): Year to update
        requested_month (int): The originally requested month (for filtering)
        requested_year (int): The originally requested year (for filtering)
    """
    for idx, table in enumerate(tables):
        cont = parameters[idx]

        data, url = read_html(cont, year, month)

        if data is None:
            logger.error(f"Error reading data from {url}: All encoding attempts failed")
            continue

        stations = data.keys()
        data = data.reset_index(drop=True)

        logger.info(f"Data shape: {data.shape}")
        logger.info(f"Requested month: {requested_month}/{requested_year}")
        logger.info("Sample data:")
        if len(data) > 0:
            logger.info(f"   First row: {data.iloc[0].tolist()}")
            logger.info(f"   Last row: {data.iloc[-1].tolist()}")
        logger.info(f"Preparing bulk insert for table {table} .....")

        # Prepare bulk data
        bulk_records = prepare_bulk_data(data, table, stations)
        
        if not bulk_records:
            logger.warning(f"No valid records found for table {table}")
            continue
        
        logger.info(f"Prepared {len(bulk_records)} records for bulk insert")
        
        # Perform bulk insert
        engine = get_db_engine()
        if engine is None:
            logger.error("Failed to create database engine")
            continue
            
        stats = bulk_insert_records(bulk_records, engine)
        
        logger.info(f"Bulk insert completed for {table}:")
        logger.info(f"  - Success: {stats['success']}")
        logger.info(f"  - Failed: {stats['failed']}")
        logger.info(f"  - Duplicate: {stats['duplicate']}")


def main() -> None:
    """
    Main function to update pollutant and meteorological data by month.
    Now receives year and month as command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Update pollutant and meteorological data by month.")
    parser.add_argument('--year', type=int, default=2015, help='Year to update (e.g., 2010)')
    parser.add_argument('--month', type=int, default=1, help='Month to update (1-12)')
    parser.add_argument('--log-level', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       help='Set the logging level')
    args = parser.parse_args()

    # Set logging level based on argument
    logger.setLevel(getattr(logging, args.log_level))

    year = args.year
    month = args.month

    if not (1 <= month <= 12):
        logger.error(f"Month must be between 1 and 12. Got {month}.")
        sys.exit(1)

    logger.info("Starting monthly data update process...")
    
    # Initialize helper object
    oz_tools = ContIOTools()

    # Update pollutant tables
    tables = oz_tools.getTables()
    parameters = oz_tools.getContaminants()
    logger.info(f"Updating pollutants tables for {year} - {month}")
    update_tables_by_month(oz_tools, tables, parameters, month, year, month, year)

    # Update meteorological tables
    tables = oz_tools.getMeteoTables()
    parameters = oz_tools.getMeteoParams()
    logger.info(f"Updating meteorological tables for {year} - {month}")
    update_tables_by_month(oz_tools, tables, parameters, month, year, month, year)
    
    logger.info(f"Monthly data update process completed for {year} - {month}!")


if __name__ == "__main__":
    main()